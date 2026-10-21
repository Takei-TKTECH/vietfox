# SPDX-License-Identifier: GPL-3.0-or-later
"""Small dialogs used by the settings pages."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, GObject, Gtk

from .helpers import key_label, pretty_hotkey

_MODIFIERS = {
    "Control_L",
    "Control_R",
    "Shift_L",
    "Shift_R",
    "Alt_L",
    "Alt_R",
    "Super_L",
    "Super_R",
    "Meta_L",
    "Meta_R",
    "Hyper_L",
    "Hyper_R",
    "Caps_Lock",
    "Num_Lock",
}


class HotkeyDialog(Adw.Dialog):
    """Records one key combination."""

    __gsignals__ = {
        "picked": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self, current: str = "") -> None:
        super().__init__()
        self.set_title("Phím tắt")
        self.set_content_width(440)
        self.set_content_height(300)
        self._current = current

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False)
        header.set_show_start_title_buttons(False)
        toolbar.add_top_bar(header)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)
        box.set_valign(Gtk.Align.CENTER)

        self._value = Gtk.Label(label=pretty_hotkey(current) or "Chưa đặt")
        self._value.add_css_class("title-1")
        self._value.add_css_class("vf-keycap")
        self._value.set_halign(Gtk.Align.CENTER)

        prompt = Gtk.Label(label="Bấm phím bạn muốn dùng")
        prompt.add_css_class("dim-label")

        self._capture = Gtk.Button(label="Bấm phím…")
        self._capture.add_css_class("pill")
        self._capture.add_css_class("suggested-action")
        self._capture.set_halign(Gtk.Align.CENTER)
        self._capture.set_size_request(220, 48)

        hint = Gtk.Label(label="Esc để huỷ · Backspace để xoá phím tắt")
        hint.add_css_class("caption")
        hint.add_css_class("dim-label")

        box.append(prompt)
        box.append(self._value)
        box.append(self._capture)
        box.append(hint)
        toolbar.set_content(box)
        self.set_child(toolbar)

        controller = Gtk.EventControllerKey()
        controller.connect("key-pressed", self._on_key)
        self._capture.add_controller(controller)
        GLib.idle_add(self._capture.grab_focus)

    def _on_key(self, _controller, keyval, _keycode, state) -> bool:
        name = Gdk.keyval_name(keyval)
        if not name:
            return False
        if name == "Escape":
            self.close()
            return True
        if name in ("BackSpace", "Delete"):
            self.emit("picked", "")
            self.close()
            return True
        if name in _MODIFIERS:
            return True

        parts = []
        if state & Gdk.ModifierType.CONTROL_MASK:
            parts.append("Control")
        if state & Gdk.ModifierType.ALT_MASK:
            parts.append("Alt")
        if state & Gdk.ModifierType.SHIFT_MASK:
            parts.append("Shift")
        if state & Gdk.ModifierType.SUPER_MASK:
            parts.append("Super")
        parts.append(name)
        combo = "+".join(parts)
        self._value.set_label(" + ".join(key_label(part) for part in parts))
        self.emit("picked", combo)
        self.close()
        return True


class FormDialog(Adw.Dialog):
    """A tiny form: a list of entry rows, optionally one drop-down."""

    __gsignals__ = {
        "submitted": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(
        self,
        title: str,
        description: str,
        fields: list[dict],
        action_label: str = "Thêm",
    ) -> None:
        super().__init__()
        self.set_title(title)
        self.set_content_width(440)
        self._fields = fields
        self._inputs: list[tuple[dict, object]] = []
        self._choices: dict[str, list[tuple[str, str]]] = {}

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False)
        header.set_show_start_title_buttons(False)
        window_title = Adw.WindowTitle(title=title)
        header.set_title_widget(window_title)

        cancel = Gtk.Button(label="Huỷ")
        cancel.connect("clicked", lambda _b: self.close())
        save = Gtk.Button(label=action_label)
        save.add_css_class("suggested-action")
        save.connect("clicked", self._on_save)
        header.pack_start(cancel)
        header.pack_end(save)
        toolbar.add_top_bar(header)

        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup()
        if description:
            group.set_description(description)
        for field in fields:
            if field.get("choices"):
                row = Adw.ComboRow(title=field["label"])
                choices = field["choices"]
                self._choices[field["name"]] = choices
                row.set_model(Gtk.StringList.new([label for _, label in choices]))
                value = field.get("value")
                selected = next(
                    (i for i, (option, _label) in enumerate(choices) if option == value), 0
                )
                row.set_selected(selected)
                group.add(row)
                self._inputs.append((field, row))
            else:
                row = Adw.EntryRow(title=field["label"])
                if field.get("placeholder"):
                    row.set_tooltip_text(field["placeholder"])
                if field.get("value"):
                    row.set_text(str(field["value"]))
                group.add(row)
                self._inputs.append((field, row))
        page.add(group)
        toolbar.set_content(page)
        self.set_child(toolbar)

        self._first = next(
            (row for field, row in self._inputs if isinstance(row, Adw.EntryRow)), None
        )
        if self._first is not None:
            self._first.connect("entry-activated", lambda _row: self._on_save(None))
            GLib.idle_add(self._first.grab_focus)

    def _on_save(self, _button) -> None:
        result = {}
        for field, row in self._inputs:
            if isinstance(row, Adw.EntryRow):
                value = row.get_text().strip()
                if field.get("required", True) and not value:
                    row.add_css_class("error")
                    row.grab_focus()
                    return
                row.remove_css_class("error")
                result[field["name"]] = value
            else:
                choices = self._choices[field["name"]]
                index = row.get_selected()
                result[field["name"]] = (
                    choices[index][0] if 0 <= index < len(choices) else choices[0][0]
                )
        self.emit("submitted", result)
        self.close()
