# SPDX-License-Identifier: GPL-3.0-or-later
"""The macros and dictionary page."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from ...core.backend import BackendError
from ..dialogs import FormDialog
from .base import Page

TIME_FORMATS = [
    ("%H:%M", "15:04 (24 giờ)"),
    ("%H:%M:%S", "15:04:05 (24 giờ)"),
    ("%I:%M %p", "03:04 PM"),
    ("%I:%M:%S %p", "03:04:05 PM"),
    ("", "Không dùng"),
]

DATE_FORMATS = [
    ("%d/%m/%Y", "31/12/2026"),
    ("%d/%m/%y", "31/12/26"),
    ("%m/%d/%Y", "12/31/2026"),
    ("%Y-%m-%d", "2026-12-31"),
    ("%y-%m-%d", "26-12-31"),
    ("", "Không dùng"),
]

SKIP_MODIFIERS = [
    ("Disabled", "Tắt"),
    ("Shift", "Shift"),
    ("Ctrl", "Ctrl"),
    ("Alt", "Alt"),
]


class MacrosPage(Page):
    ident = "macros"
    title = "Gõ tắt & Từ điển"
    icon = "accessories-dictionary-symbolic"

    def build(self) -> None:
        self._macro_rows: list[Gtk.Widget] = []
        self._word_rows: list[Gtk.Widget] = []

        group = self.group(
            "Gõ tắt",
            "Gõ chữ viết tắt để chèn cả cụm từ. Dùng $TIME và $DATE trong nội dung để chèn giờ, ngày.",
        )
        self.add(
            group,
            self.switch(
                "EnableMacro",
                "Bật gõ tắt",
                True,
                keywords="go tat macro",
            ),
        )
        self.add(
            group,
            self.switch(
                "CapitalizeMacro",
                "Gõ tắt chữ hoa",
                "Giữ chữ hoa khi viết tắt ở đầu câu.",
                True,
                keywords="go tat chu hoa capitalize",
            ),
        )
        self.add(
            group,
            self.switch(
                "EnableMacroInOffMode",
                "Cho phép gõ tắt ở chế độ Tắt",
                False,
                keywords="go tat che do tat off",
            ),
        )
        self.add(
            group,
            self.combo(
                "MacroSkipTriggerModifier",
                "Phím bỏ qua gõ tắt",
                SKIP_MODIFIERS,
                subtitle="Giữ phím này để gõ đúng chữ viết tắt cho từ hiện tại.",
                default="Disabled",
                keywords="bo qua go tat shift ctrl alt",
            ),
        )
        self.add(
            group,
            self.combo(
                "TimeFormat",
                "Định dạng giờ",
                TIME_FORMATS,
                default="%H:%M",
                keywords="dinh dang gio time",
            ),
        )
        self.add(
            group,
            self.combo(
                "DateFormat",
                "Định dạng ngày",
                DATE_FORMATS,
                default="%d/%m/%Y",
                keywords="dinh dang ngay date",
            ),
        )

        self._macro_group = self.group(
            "Danh sách gõ tắt",
            "Bấm vào một dòng để sửa. Gõ tắt không phân biệt chữ hoa, chữ thường.",
        )
        self._add_macro_button = Adw.ButtonRow(title="Thêm gõ tắt")
        self._add_macro_button.set_start_icon_name("list-add-symbolic")
        self._add_macro_button.connect("activated", lambda _row: self._add_macro())
        self.track(self._add_macro_button, "them go tat macro")

        self._word_group = self.group("Từ điển tuỳ chỉnh")
        self.add(
            self._word_group,
            self.switch(
                "EnableDictionary",
                "Dùng từ điển tuỳ chỉnh",
                "Từ trong danh sách này không bị coi là gõ sai.",
                False,
                keywords="tu dien dictionary tu dien tuy chinh",
            ),
        )
        add_word = Adw.ButtonRow(title="Thêm từ")
        add_word.set_start_icon_name("list-add-symbolic")
        add_word.connect("activated", lambda _row: self._add_word())
        self._add_word_button = add_word
        self.track(add_word, "them tu dictionary")

        self._reload_macros()
        self._reload_words()

    # ----------------------------------------------------------------- macros
    def _reload_macros(self) -> None:
        for row in self._macro_rows:
            self._macro_group.remove(row)
        self._forget(self._macro_rows)
        self._macro_rows = []
        macros = self.window.backend.get_macros()
        if not macros:
            empty = Adw.ActionRow(
                title="Chưa có gõ tắt nào",
                subtitle="Thêm cặp viết tắt để gõ nhanh những cụm từ hay dùng.",
            )
            empty.set_sensitive(False)
            self._macro_group.add(empty)
            self._macro_rows.append(empty)
            self.track(empty, "chua co go tat")
        else:
            for index, macro in enumerate(macros):
                key = macro.get("Key", "")
                value = macro.get("Value", "")
                row = Adw.ActionRow(title=key, subtitle=value)
                row.set_activatable(True)
                row.connect("activated", lambda _row, i=index: self._edit_macro(i))
                remove = Gtk.Button(icon_name="user-trash-symbolic")
                remove.add_css_class("flat")
                remove.set_valign(Gtk.Align.CENTER)
                remove.set_tooltip_text("Xoá gõ tắt")
                remove.connect("clicked", lambda _button, i=index: self._delete_macro(i))
                row.add_suffix(remove)
                self._macro_group.add(row)
                self._macro_rows.append(row)
                self.track(row, "go tat macro " + key + " " + value)
        if self._add_macro_button.get_parent():
            self._macro_group.remove(self._add_macro_button)
        self._macro_group.add(self._add_macro_button)

    def _add_macro(self) -> None:
        self._macro_dialog(None, -1)

    def _edit_macro(self, index: int) -> None:
        macros = self.window.backend.get_macros()
        if 0 <= index < len(macros):
            self._macro_dialog(macros[index], index)

    def _macro_dialog(self, macro: dict | None, index: int) -> None:
        dialog = FormDialog(
            "Sửa gõ tắt" if macro else "Thêm gõ tắt",
            "Chữ viết tắt được thay bằng nội dung khi bạn gõ xong từ và nhấn dấu cách.",
            [
                {
                    "name": "key",
                    "label": "Chữ viết tắt",
                    "placeholder": "kg",
                    "value": macro.get("Key", "") if macro else "",
                },
                {
                    "name": "value",
                    "label": "Nội dung",
                    "placeholder": "khô gà",
                    "value": macro.get("Value", "") if macro else "",
                },
            ],
            "Lưu" if macro else "Thêm",
        )

        def submitted(_dialog, data) -> None:
            self._save_macro(data["key"], data["value"], index)

        dialog.connect("submitted", submitted)
        dialog.present(self.window)

    def _save_macro(self, key: str, value: str, index: int) -> None:
        macros = self.window.backend.get_macros()
        duplicate = next(
            (i for i, item in enumerate(macros) if item.get("Key", "").casefold() == key.casefold()),
            None,
        )
        if duplicate is not None and duplicate != index:
            self.window.show_error(f'Gõ tắt “{key}” đã có.')
            return
        if index >= 0 and index < len(macros):
            macros[index] = {"Key": key, "Value": value}
        else:
            macros.append({"Key": key, "Value": value})
        try:
            self.window.backend.set_macros(macros)
        except BackendError as error:
            self.window.show_error(str(error))
            return
        self._reload_macros()
        self.window.show_toast(f'Đã lưu gõ tắt “{key}”.')

    def _delete_macro(self, index: int) -> None:
        macros = self.window.backend.get_macros()
        if not (0 <= index < len(macros)):
            return
        key = macros[index].get("Key", "")

        def confirmed() -> None:
            try:
                self.window.backend.set_macros(macros[:index] + macros[index + 1 :])
            except BackendError as error:
                self.window.show_error(str(error))
                return
            self._reload_macros()
            self.window.show_toast(f'Đã xoá gõ tắt “{key}”.')

        self.window.confirm(
            f"Xoá gõ tắt “{key}”?",
            "Bạn có thể thêm lại sau.",
            "Xoá",
            confirmed,
            destructive=True,
        )

    # ------------------------------------------------------------- dictionary
    def _reload_words(self) -> None:
        for row in self._word_rows:
            self._word_group.remove(row)
        self._forget(self._word_rows)
        self._word_rows = []
        words = self.window.backend.get_dictionary()
        if not words:
            empty = Adw.ActionRow(
                title="Chưa có từ nào",
                subtitle="Thêm tên riêng hoặc từ chuyên ngành để không bị báo gõ sai.",
            )
            empty.set_sensitive(False)
            self._word_group.add(empty)
            self._word_rows.append(empty)
            self.track(empty, "chua co tu dictionary")
        else:
            for index, word in enumerate(words):
                row = Adw.ActionRow(title=word)
                remove = Gtk.Button(icon_name="user-trash-symbolic")
                remove.add_css_class("flat")
                remove.set_valign(Gtk.Align.CENTER)
                remove.set_tooltip_text("Xoá từ")
                remove.connect("clicked", lambda _button, i=index: self._delete_word(i))
                row.add_suffix(remove)
                self._word_group.add(row)
                self._word_rows.append(row)
                self.track(row, "tu dien dictionary " + word)
        if self._add_word_button.get_parent():
            self._word_group.remove(self._add_word_button)
        self._word_group.add(self._add_word_button)

    def _add_word(self) -> None:
        dialog = FormDialog(
            "Thêm từ",
            "Từ này sẽ được coi là hợp lệ khi kiểm tra chính tả.",
            [{"name": "word", "label": "Từ", "placeholder": "Vietfox"}],
            "Thêm",
        )

        def submitted(_dialog, data) -> None:
            word = data["word"].strip()
            if " " in word:
                self.window.show_error("Từ điển chỉ nhận một từ, không có dấu cách.")
                return
            words = self.window.backend.get_dictionary()
            if any(existing.casefold() == word.casefold() for existing in words):
                self.window.show_error(f'Từ “{word}” đã có trong từ điển.')
                return
            try:
                self.window.backend.set_dictionary(words + [word])
            except BackendError as error:
                self.window.show_error(str(error))
                return
            self._reload_words()
            self.window.show_toast(f'Đã thêm từ “{word}”.')

        dialog.connect("submitted", submitted)
        dialog.present(self.window)

    def _delete_word(self, index: int) -> None:
        words = self.window.backend.get_dictionary()
        if not (0 <= index < len(words)):
            return
        word = words[index]
        try:
            self.window.backend.set_dictionary(words[:index] + words[index + 1 :])
        except BackendError as error:
            self.window.show_error(str(error))
            return
        self._reload_words()
        self.window.show_toast(f'Đã xoá từ “{word}”.')

    def _forget(self, rows: list[Gtk.Widget]) -> None:
        ids = {id(row) for row in rows}
        self.items = [item for item in self.items if id(item[0]) not in ids]
