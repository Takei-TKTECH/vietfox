# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared behaviour for the settings pages."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk

from ...core.backend import BackendError
from ...core.store import BOOL, HOTKEY, INT, TEXT
from ..helpers import pretty_hotkey

MODE_OPTIONS = [
    ("Sen", "Mặc định"),
    ("Preedit", "Gạch chân"),
    ("Emoji Picker", "Chọn emoji"),
    ("OFF", "Tắt"),
]


def _set_guard(widget, guard: bool) -> None:
    widget._vf_guard = guard


class Page:
    """One page of the window: grouped rows plus searchable metadata."""

    ident = ""
    title = ""
    icon = ""

    def __init__(self, window) -> None:
        self.window = window
        self.store = window.store
        self.widget = Adw.PreferencesPage()
        self.items: list[tuple[object, str, str, str]] = []
        self.rows: dict[str, object] = {}
        self._pending: dict[str, tuple] = {}
        self.build()

    # ------------------------------------------------------------------ build
    def build(self) -> None:
        raise NotImplementedError

    def group(self, title: str = "", description: str = "") -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup()
        if title:
            group.set_title(title)
        if description:
            group.set_description(description)
        self.widget.add(group)
        return group

    def track(self, row, keywords: str = "", title: str = "", subtitle: str = ""):
        if not title:
            title = row.get_title() if hasattr(row, "get_title") else ""
        if not subtitle:
            subtitle = row.get_subtitle() if hasattr(row, "get_subtitle") else ""
        self.items.append((row, title or "", subtitle or "", keywords))
        return row

    # ----------------------------------------------------------------- saving
    def _commit(self, key: str, title: str, value, apply) -> None:
        self._cancel_pending(key)
        try:
            old = self.store.set(key, value)
        except BackendError as error:
            apply(self.store.get(key))
            self.window.show_error(str(error))
            return
        self.window.sync_switch_setting(key, bool(value), self)
        self.window.show_saved(title, lambda: self._revert(key, title, old, apply))

    def _revert(self, key: str, title: str, old, apply) -> None:
        try:
            self.store.set(key, old)
        except BackendError as error:
            self.window.show_error(str(error))
            return
        apply(old)
        self.window.sync_switch_setting(key, bool(old), self)
        self.window.show_undone(title)

    def _cancel_pending(self, key: str) -> None:
        pending = self._pending.pop(key, None)
        if pending:
            GLib.source_remove(pending[0])

    def flush(self) -> None:
        for key in list(self._pending):
            source, schedule = self._pending.pop(key)
            GLib.source_remove(source)
            schedule()

    def discard_pending(self) -> None:
        """Drops edits that have not been written yet, e.g. before rebuilding a page."""
        for key in list(self._pending):
            source, _schedule = self._pending.pop(key)
            GLib.source_remove(source)

    # ------------------------------------------------------------------ rows
    def switch(
        self,
        key: str,
        title: str,
        subtitle: str | bool = "",
        default: bool = False,
        keywords: str = "",
    ) -> Adw.SwitchRow:
        if isinstance(subtitle, bool):
            # Pages may pass the default as the third positional argument.
            default = subtitle
            subtitle = ""
        self.store.register(key, BOOL, default, title)
        row = Adw.SwitchRow(title=title)
        if subtitle:
            row.set_subtitle(subtitle)
        row.set_active(self.store.get(key))
        _set_guard(row, False)

        def apply(value) -> None:
            _set_guard(row, True)
            row.set_active(bool(value))
            _set_guard(row, False)

        def changed(widget, _pspec) -> None:
            if getattr(row, "_vf_guard", False):
                return
            self._commit(key, title, row.get_active(), apply)

        row.connect("notify::active", changed)
        self.rows[key] = row
        return row

    def combo(
        self,
        key: str,
        title: str,
        options: list[tuple[str, str]],
        subtitle: str = "",
        default: str = "",
        keywords: str = "",
    ) -> Adw.ComboRow:
        self.store.register(key, TEXT, default, title)
        row = Adw.ComboRow(title=title)
        if subtitle:
            row.set_subtitle(subtitle)
        row.set_model(Gtk.StringList.new([label for _, label in options]))
        current = self.store.get(key)
        selected = next(
            (index for index, (value, _) in enumerate(options) if value == current), 0
        )
        _set_guard(row, True)
        row.set_selected(selected)
        _set_guard(row, False)

        def apply(value) -> None:
            index = next(
                (i for i, (option, _) in enumerate(options) if option == value), 0
            )
            _set_guard(row, True)
            row.set_selected(index)
            _set_guard(row, False)

        def changed(widget, _pspec) -> None:
            if getattr(row, "_vf_guard", False):
                return
            index = row.get_selected()
            if 0 <= index < len(options):
                self._commit(key, title, options[index][0], apply)

        row.connect("notify::selected", changed)
        self.rows[key] = row
        return row

    def spin(
        self,
        key: str,
        title: str,
        default: int,
        lower: int = 0,
        upper: int = 10000,
        step: int = 1,
        subtitle: str = "",
    ) -> Adw.SpinRow:
        self.store.register(key, INT, default, title)
        adjustment = Gtk.Adjustment(
            value=self.store.get(key),
            lower=lower,
            upper=upper,
            step_increment=step,
            page_increment=step * 10,
        )
        row = Adw.SpinRow(adjustment=adjustment, climb_rate=1, digits=0)
        row.set_title(title)
        if subtitle:
            row.set_subtitle(subtitle)
        _set_guard(row, False)

        def apply(value) -> None:
            _set_guard(row, True)
            row.set_value(int(value))
            _set_guard(row, False)

        def changed(widget, _pspec) -> None:
            if getattr(row, "_vf_guard", False):
                return
            self._commit(key, title, int(row.get_value()), apply)

        row.connect("notify::value", changed)
        self.rows[key] = row
        return row

    def entry(
        self,
        key: str,
        title: str,
        default: str = "",
        subtitle: str = "",
        placeholder: str = "",
        delay: int = 500,
    ) -> Adw.ActionRow:
        self.store.register(key, TEXT, default, title)
        row = Adw.ActionRow(title=title)
        if subtitle:
            row.set_subtitle(subtitle)
        field = Gtk.Entry()
        field.set_text(self.store.get(key))
        field.set_width_chars(12)
        field.set_max_width_chars(34)
        field.set_hexpand(True)
        field.set_valign(Gtk.Align.CENTER)
        if placeholder:
            field.set_placeholder_text(placeholder)
        row.add_suffix(field)

        def apply(value) -> None:
            self._cancel_pending(key)
            _set_guard(row, True)
            field.set_text(str(value))
            _set_guard(row, False)

        def schedule() -> bool:
            if getattr(row, "_vf_guard", False):
                return False
            self._pending.pop(key, None)
            self._commit(key, title, field.get_text(), apply)
            return False

        def changed(widget, _pspec) -> None:
            if getattr(row, "_vf_guard", False):
                return
            self._cancel_pending(key)
            source = GLib.timeout_add(delay, schedule)
            self._pending[key] = (source, schedule)

        field.connect("notify::text", changed)
        self.rows[key] = row
        return row

    def hotkey(
        self,
        key: str,
        title: str,
        default: str = "",
        subtitle: str = "",
    ) -> Adw.ActionRow:
        self.store.register(key, HOTKEY, default, title)
        row = Adw.ActionRow(title=title)
        if subtitle:
            row.set_subtitle(subtitle)
        button = Gtk.Button()
        button.add_css_class("vf-keycap")
        button.set_valign(Gtk.Align.CENTER)

        def refresh(value=None) -> None:
            current = self.store.get(key) if value is None else value
            label = pretty_hotkey(str(current))
            button.set_label(label or "Chưa đặt")
            if label:
                button.remove_css_class("dim-label")
            else:
                button.add_css_class("dim-label")

        refresh()
        row.add_suffix(button)

        def apply(value) -> None:
            refresh(value)

        def clicked(_button) -> None:
            from ..dialogs import HotkeyDialog

            dialog = HotkeyDialog(self.store.get(key))

            def on_done(value: str | None) -> None:
                if value is None:
                    return
                try:
                    old = self.store.set(key, value)
                except BackendError as error:
                    self.window.show_error(str(error))
                    return
                apply(value)
                self.window.show_saved(
                    title, lambda: self._revert(key, title, old, apply)
                )

            dialog.connect("picked", lambda _dialog, value: on_done(value))
            dialog.present(self.window)

        button.connect("clicked", clicked)
        self.rows[key] = row
        return row

    # ------------------------------------------------------------------ misc
    def add(self, group, row, keywords: str = ""):
        group.add(row)
        self.track(row, keywords)
        return row
