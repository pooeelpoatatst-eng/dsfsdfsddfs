from app.modules.help import help_pages, module_table
from app.userbot.registry import CommandMeta


async def handler(_: object) -> None:
    pass


def test_module_table_wraps_commands_in_rows() -> None:
    metas = [CommandMeta(name, (), "Игры", "", "", handler) for name in ("game2048", "rps", "tictactoe", "wordle")]
    table = module_table("Игры", metas)
    assert "Модуль" in table and ".game2048" in table and "┌" in table


def test_help_menu_uses_html_pre_tables() -> None:
    pages = help_pages(limit=500)
    assert "<pre>" in pages[0]
    assert all(len(page) <= 600 for page in pages)
