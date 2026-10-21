# SPDX-License-Identifier: GPL-3.0-or-later
"""Frequently used feature switches."""

from __future__ import annotations

from .base import Page


class QuickPage(Page):
    ident = "quick"
    title = "Bật/tắt nhanh"
    icon = "view-grid-symbolic"

    def build(self) -> None:
        features = self.group(
            "Tính năng bộ gõ",
            "Bật hoặc tắt nhanh các tính năng thường dùng. Thay đổi được lưu ngay.",
        )
        for key, title, subtitle, default, keywords in [
            (
                "SpellCheck",
                "Kiểm tra chính tả",
                "Dùng từ điển để nhận ra từ không hợp lệ.",
                True,
                "chinh ta spell check",
            ),
            (
                "AutoNonVnRestore",
                "Tự khôi phục từ gõ sai",
                "Trả lại từ không hợp lệ đúng như đã gõ.",
                True,
                "khoi phuc tu go sai restore",
            ),
            (
                "EnableMacro",
                "Gõ tắt",
                "Gõ từ viết tắt để chèn cụm từ đã thiết lập.",
                True,
                "go tat macro",
            ),
            (
                "CapitalizeMacro",
                "Viết hoa gõ tắt",
                "Giữ chữ hoa khi gõ tắt ở đầu câu.",
                True,
                "viet hoa go tat capitalize",
            ),
            (
                "EnableDictionary",
                "Từ điển cá nhân",
                "Không coi các từ trong từ điển cá nhân là từ gõ sai.",
                False,
                "tu dien ca nhan dictionary",
            ),
        ]:
            self.add(
                features,
                self.switch(key, title, subtitle, default, keywords=keywords),
            )
