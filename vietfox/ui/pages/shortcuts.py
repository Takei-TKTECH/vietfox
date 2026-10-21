# SPDX-License-Identifier: GPL-3.0-or-later
"""The keys page: mode switching and the tray icon."""

from __future__ import annotations

import shutil
import subprocess

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk

from ...core.backend import BackendError
from ...core.store import BOOL, TEXT
from .base import Page

MODES = [
    ("Sen", "Gõ Sen", "1"),
    ("Preedit", "Gạch chân", "q"),
    ("Emoji", "Chọn emoji", "w"),
    ("Off", "Tắt", "e"),
    ("Default", "Gõ mặc định", "r"),
]


class ShortcutsPage(Page):
    ident = "shortcuts"
    title = "Phím"
    icon = "preferences-desktop-keyboard-shortcuts-symbolic"

    def build(self) -> None:
        self._mode_pending: list[int] = []
        switch = self.group(
            "Chuyển chế độ",
            "Dùng phím tắt của fcitx5 để chuyển nhanh giữa các chế độ.",
        )
        self.add(
            switch,
            self.hotkey(
                "ModeMenuKey",
                "Mở menu chế độ",
                default="grave",
                subtitle="Bấm để mở menu chọn chế độ.",
            ),
            "phim tat menu che do",
        )
        self.add(
            switch,
            self.hotkey(
                "CycleModeKey",
                "Chuyển nhanh chế độ",
                default="",
                subtitle="Mỗi lần bấm chuyển sang chế độ kế tiếp.",
            ),
            "phim tat chuyen nhanh che do",
        )

        menu = self.group(
            "Menu chế độ",
            "Chọn chế độ hiện trong menu và phím tắt riêng của từng chế độ.",
        )
        for ident, label, shortcut in MODES:
            menu.add(self._mode_row(ident, label, shortcut))

        icons = self.group("Biểu tượng")
        self.add(
            icons,
            self.combo(
                "IconTheme",
                "Màu biểu tượng",
                [("Auto", "Tự động"), ("Light", "Sáng"), ("Dark", "Tối")],
                default="Auto",
                keywords="mau bieu tuong icon theme",
            ),
        )
        self.add(
            icons,
            self.switch(
                "UseLotusIcons",
                "Dùng biểu tượng trạng thái Vietfox",
                "Hiện trạng thái gõ trên khay hệ thống.",
                True,
                keywords="bieu tuong trang thai khay he thong",
            ),
        )

        advanced = self.group(
            "Nâng cao",
            "Chỉ cần đổi khi bạn muốn tuỳ biến sâu.",
        )
        order = self.entry(
            "ModeOrder",
            "Thứ tự chế độ",
            default="Sen,Preedit,Emoji,Off,Default",
            subtitle="Các chế độ cách nhau bằng dấu phẩy.",
            placeholder="Sen,Preedit,Emoji,Off,Default",
        )
        self.add(advanced, order, "thu tu che do mode order")
        self.add(
            advanced,
            self.switch(
                "EnableCustomKeymap",
                "Bật keymap tuỳ chỉnh",
                "Keymap được sửa trong phần cài đặt bàn phím của fcitx5.",
                False,
                keywords="keymap tuy chinh ban phim",
            ),
        )
        open_fcitx = Adw.ButtonRow(title="Mở cài đặt bàn phím fcitx5")
        open_fcitx.set_start_icon_name("preferences-system-symbolic")
        open_fcitx.connect("activated", lambda _row: self._open_fcitx())
        advanced.add(open_fcitx)
        self.track(open_fcitx, "mo cai dat ban phim fcitx5 keymap")

    # ------------------------------------------------------------------ rows
    def _mode_row(self, ident: str, label: str, shortcut: str) -> Adw.ActionRow:
        show_key = f"ShowMode{ident}"
        shortcut_key = f"Shortcut{ident}"
        self.store.register(show_key, BOOL, True, label)
        self.store.register(shortcut_key, TEXT, shortcut, f"Phím tắt {label}")

        row = Adw.ActionRow(title=label)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)

        entry = Gtk.Entry()
        entry.set_width_chars(5)
        entry.set_max_width_chars(8)
        entry.set_alignment(0.5)
        entry.set_tooltip_text("Phím tắt trong menu chế độ")
        box.append(entry)

        toggle = Gtk.Switch()
        toggle.set_valign(Gtk.Align.CENTER)
        toggle.set_tooltip_text("Hiện chế độ này trong menu")
        box.append(toggle)
        row.add_suffix(box)

        guard = {"on": False}
        pending = {"source": 0}

        def apply(show, key) -> None:
            guard["on"] = True
            toggle.set_active(bool(show))
            entry.set_text(str(key))
            guard["on"] = False

        def revert(values: dict) -> None:
            apply(values.get(show_key, True), values.get(shortcut_key, ""))

        def save() -> None:
            if pending["source"] in self._mode_pending:
                self._mode_pending.remove(pending["source"])
            pending["source"] = 0
            if guard["on"]:
                return
            values = {show_key: toggle.get_active(), shortcut_key: entry.get_text()}
            try:
                old = self.store.set_many(values)
            except BackendError as error:
                revert({show_key: self.store.get(show_key), shortcut_key: self.store.get(shortcut_key)})
                self.window.show_error(str(error))
                return
            self.window.show_saved(label, lambda: self._undo_mode(values, old))

        def schedule() -> bool:
            if pending["source"]:
                if pending["source"] in self._mode_pending:
                    self._mode_pending.remove(pending["source"])
                GLib.source_remove(pending["source"])
            pending["source"] = GLib.timeout_add(500, save)
            self._mode_pending.append(pending["source"])
            return False

        def on_toggle(_switch, _pspec) -> None:
            if guard["on"]:
                return
            if pending["source"]:
                if pending["source"] in self._mode_pending:
                    self._mode_pending.remove(pending["source"])
                GLib.source_remove(pending["source"])
                pending["source"] = 0
            save()

        def on_entry(_entry, _pspec) -> None:
            if guard["on"]:
                return
            schedule()

        apply(self.store.get(show_key), self.store.get(shortcut_key))
        toggle.connect("notify::active", on_toggle)
        entry.connect("notify::text", on_entry)
        self.track(row, f"che do {label} phim tat hien thi")
        return row

    def discard_pending(self) -> None:
        super().discard_pending()
        for source in self._mode_pending:
            GLib.source_remove(source)
        self._mode_pending.clear()

    def _undo_mode(self, values: dict, old: dict) -> None:
        try:
            self.store.set_many(old)
        except BackendError as error:
            self.window.show_error(str(error))
            return
        # Rebuild the page so both controls show the restored values.
        self.window.reload_pages()
        self.window.show_undone("menu chế độ")

    def _open_fcitx(self) -> None:
        program = shutil.which("fcitx5-configtool")
        if not program:
            self.window.show_error("Chưa cài fcitx5-configtool trên máy này.")
            return
        try:
            subprocess.Popen([program])
        except OSError as error:
            self.window.show_error(str(error))
