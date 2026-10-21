# SPDX-License-Identifier: GPL-3.0-or-later
"""Small text helpers shared by the window and its pages."""

from __future__ import annotations

import unicodedata

import gi

gi.require_version("Gdk", "4.0")
from gi.repository import Gdk

_HOTKEY_NAMES = {
    "Control": "Ctrl",
    "Alt": "Alt",
    "Shift": "Shift",
    "Super": "Super",
    "Meta": "Super",
    "grave": "`",
    "asciitilde": "~",
    "minus": "-",
    "underscore": "_",
    "equal": "=",
    "plus": "+",
    "bracketleft": "[",
    "braceleft": "{",
    "bracketright": "]",
    "braceright": "}",
    "backslash": "\\",
    "bar": "|",
    "semicolon": ";",
    "colon": ":",
    "apostrophe": "'",
    "quotedbl": '"',
    "comma": ",",
    "less": "<",
    "period": ".",
    "greater": ">",
    "slash": "/",
    "question": "?",
    "space": "Space",
    "Return": "Enter",
    "KP_Enter": "Enter",
    "BackSpace": "Backspace",
    "Delete": "Delete",
    "Insert": "Insert",
    "Escape": "Esc",
    "Tab": "Tab",
    "ISO_Left_Tab": "Tab",
    "Control_L": "Ctrl",
    "Control_R": "Ctrl",
    "Shift_L": "Shift",
    "Shift_R": "Shift",
    "Alt_L": "Alt",
    "Alt_R": "Alt",
    "Super_L": "Super",
    "Super_R": "Super",
}


def normalize(text: str) -> str:
    """Case- and accent-insensitive text used for searching."""
    text = unicodedata.normalize("NFD", text.casefold())
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text.replace("đ", "d")


def key_label(name: str) -> str:
    if not name:
        return ""
    if name in _HOTKEY_NAMES:
        return _HOTKEY_NAMES[name]
    if len(name) == 1:
        return name.upper()
    keyval = Gdk.keyval_from_name(name)
    if keyval:
        char = Gdk.keyval_to_unicode(keyval)
        if char and char.isprintable() and not char.isspace():
            return char
        label = Gdk.keyval_name(keyval)
        if label:
            return _HOTKEY_NAMES.get(label, label)
    return name


def pretty_hotkey(value: str) -> str:
    """'Control+grave' -> 'Ctrl + `'."""
    if not value:
        return ""
    combos = []
    for combo in value.split():
        combos.append(" + ".join(key_label(part) for part in combo.split("+")))
    return "  ".join(combos)


def mode_label(mode: str) -> str:
    return {"2": "Gõ Sen", "5": "Gạch chân", "6": "Chọn emoji", "0": "Tắt"}.get(
        str(mode), "Gõ Sen"
    )
