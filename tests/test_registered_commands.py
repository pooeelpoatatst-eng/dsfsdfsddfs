from app.userbot.module_loader import ModuleLoader
from app.userbot.registry import commands


def test_safe_core_filters_notes_chat_and_contacts_are_registered() -> None:
    ModuleLoader().load_all()
    names = {meta.name for meta in commands()}
    expected = {
        "settings", "setprefix", "lang", "preset", "addalias", "delalias", "aliases",
        "filter", "stop", "stopall", "filters", "gfilter", "gstop", "gstopall", "gfilters", "allfilters",
        "save", "note", "notes", "delnote", "delallnotes",
        "block", "unblock", "addcontact", "delcontact", "report",
        "invite", "kickme", "members", "admins", "bots", "link", "common",
    }
    assert expected <= names
