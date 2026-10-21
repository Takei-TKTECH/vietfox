# SPDX-License-Identifier: GPL-3.0-or-later
"""The about page."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from ...version import VERSION
from .base import Page


class AboutPage(Page):
    ident = "about"
    title = "Giới thiệu"
    icon = "help-about-symbolic"

    def build(self) -> None:
        hero_group = Adw.PreferencesGroup()
        hero_row = Adw.ActionRow()
        hero_row.set_activatable(False)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_halign(Gtk.Align.CENTER)
        box.set_margin_top(18)
        box.set_margin_bottom(22)
        icon = Gtk.Image.new_from_icon_name("io.github.vietfox.Vietfox")
        icon.set_pixel_size(96)
        name = Gtk.Label(label="Vietfox")
        name.add_css_class("title-1")
        tagline = Gtk.Label(label="Bộ gõ tiếng Việt cho Linux")
        tagline.add_css_class("dim-label")
        version = Gtk.Label(label=f"Phiên bản {VERSION}")
        version.add_css_class("caption")
        version.add_css_class("dim-label")
        box.append(icon)
        box.append(name)
        box.append(tagline)
        box.append(version)
        hero_row.set_child(box)
        hero_group.add(hero_row)
        self.widget.add(hero_group)

        info = self.group("Thông tin")
        self.add(info, Adw.ActionRow(title="Phiên bản", subtitle=VERSION), "phien ban version")
        self.add(
            info,
            Adw.ActionRow(
                title="Nền tảng",
                subtitle="fcitx5 trên Linux — GNOME, KDE, Xfce, Sway và Hyprland",
            ),
            "nen tang fcitx5 linux gnome kde",
        )
        self.add(
            info,
            Adw.ActionRow(
                title="Giấy phép",
                subtitle="GNU General Public License 3.0 hoặc mới hơn",
            ),
            "giay phep license gpl",
        )
        self.add(
            info,
            Adw.ActionRow(
                title="Cấu hình",
                subtitle="Giữ nguyên cấu hình, từ điển và gõ tắt bạn đã dùng",
            ),
            "cau hinh addon ngosen",
        )

        credits = self.group("Ghi công", "Vietfox đứng trên vai những dự án mở này.")
        self._credit(
            credits,
            "Ngó Sen",
            "Bộ gõ tiếng Việt mà Vietfox dựa trên, của Nguyễn Hoàng Kỳ.",
            "https://github.com/ngosen/ngosen",
        )
        self._credit(
            credits,
            "fcitx5",
            "Khung bộ gõ dùng chung cho các desktop Linux.",
            "https://fcitx-im.org",
        )
        self._credit(
            credits,
            "Bamboo",
            "Phần xử lý tiếng Việt.",
            "https://github.com/BambooEngine/ibus-bamboo",
        )
        self._credit(
            credits,
            "GNOME và libadwaita",
            "Giao diện theo chuẩn ứng dụng của GNOME.",
            "https://gnome.org",
        )

        legal = Adw.ButtonRow(title="Giấy phép và ghi công")
        legal.set_start_icon_name("help-about-symbolic")
        legal.connect("activated", lambda _row: self.window.show_about())
        credits.add(legal)
        self.track(legal, "giay phep ghi cong about")

    def _credit(self, group, title: str, subtitle: str, uri: str) -> None:
        row = Adw.ActionRow(title=title, subtitle=subtitle)
        link = Gtk.LinkButton(uri=uri, label="Mở")
        link.add_css_class("flat")
        link.set_valign(Gtk.Align.CENTER)
        row.add_suffix(link)
        group.add(row)
        self.track(row, "ghi cong credit " + title)
