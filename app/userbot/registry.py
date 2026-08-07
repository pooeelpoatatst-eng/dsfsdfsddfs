from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

Handler = Callable[[Any], Awaitable[None]]


@dataclass(frozen=True)
class CommandMeta:
    name: str
    aliases: tuple[str, ...]
    category: str
    description: str
    usage: str
    handler: Handler
    requires_ai: bool = False
    requires_reply: bool = False
    admin_only: bool = False
    module: str = "core"


REGISTRY: dict[str, CommandMeta] = {}


def command(*, name: str, aliases: list[str] | None = None, category: str, description: str, usage: str, requires_ai: bool = False, requires_reply: bool = False, admin_only: bool = False) -> Callable[[Handler], Handler]:
    def decorator(handler: Handler) -> Handler:
        meta = CommandMeta(name, tuple(aliases or []), category, description, usage, handler, requires_ai, requires_reply, admin_only, handler.__module__.rsplit(".", 1)[-1])
        for key in (name, *meta.aliases):
            if key in REGISTRY: raise RuntimeError(f"Duplicate userbot command: {key}")
            REGISTRY[key] = meta
        return handler
    return decorator


def commands() -> list[CommandMeta]:
    return list({meta.name: meta for meta in REGISTRY.values()}.values())
