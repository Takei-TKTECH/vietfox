# SPDX-License-Identifier: GPL-3.0-or-later
"""Vietfox application object."""

from __future__ import annotations

import os
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
from gi.repository import Adw, Gdk, Gio, Gtk

from .version import APP_ID, APP_NAME, VERSION
from .ui.window import VietfoxWindow


class VietfoxApplication(Adw.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self._window: VietfoxWindow | None = None

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)
        Gtk.Window.set_default_icon_name(APP_ID)
        display = Gdk.Display.get_default()
        if display is not None:
            icon_theme = Gtk.IconTheme.get_for_display(display)
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            if os.path.isdir(data_dir):
                icon_theme.add_search_path(data_dir)
        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", lambda *_args: self.quit())
        self.add_action(action)

    def do_activate(self) -> None:
        if self._window is None:
            self._window = VietfoxWindow(self)
        self._window.present()


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv if argv is None else argv)
    if "--version" in args:
        print(f"{APP_NAME} {VERSION}")
        return 0
    if "--help" in args or "-h" in args:
        print(
            f"{APP_NAME} {VERSION}\n"
            "Bộ gõ tiếng Việt cho Linux.\n\n"
            "Cách dùng: vietfox [--version]\n"
            "Cài đặt được lưu ngay khi thay đổi."
        )
        return 0
    app = VietfoxApplication()
    return app.run(args)
