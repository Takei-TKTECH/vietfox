# SPDX-License-Identifier: GPL-3.0-or-later
"""The about page."""

from __future__ import annotations

import gi

gi.require_version("Adw", "1")
from gi.repository import Adw

from .base import Page


class AboutPage(Page):
    ident = "about"
    title = "Giới thiệu"
    icon = "help-about-symbolic"

    def build(self) -> None:
        group = self.group()
        row = Adw.ActionRow(title="Vietfox được phát triển mới từ Ngó Sen")
        group.add(row)
        self.track(row, "gioi thieu vietfox ngo sen")
