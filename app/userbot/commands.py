from __future__ import annotations

import shlex
from dataclasses import dataclass

from app.userbot.registry import CommandMeta, REGISTRY


@dataclass(frozen=True)
class ParsedCommand:
    name: str
    args: list[str]
    raw_args: str
    meta: CommandMeta | None


def parse_command(text: str, prefix: str = ".") -> ParsedCommand | None:
    if not prefix or len(prefix) > 3 or not text.startswith(prefix) or len(text) <= len(prefix):
        return None
    body = text[len(prefix):].strip()
    if not body or body[0] in "/." or "." in body.split(maxsplit=1)[0]:
        return None
    try:
        parts = shlex.split(body)
    except ValueError:
        return None
    if not parts: return None
    name = parts[0].lower()
    raw_args = body[len(parts[0]):].strip()
    return ParsedCommand(name, parts[1:], raw_args, REGISTRY.get(name))
