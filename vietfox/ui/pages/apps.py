# SPDX-License-Identifier: GPL-3.0-or-later
"""Per-application typing modes."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from ...core.backend import BackendError
from ..dialogs import FormDialog
from .base import Page

RULE_MODES = [("2", "Mặc định"), ("5", "Gạch chân"), ("6", "Chọn emoji"), ("0", "Tắt")]


class AppsPage(Page):
    ident = "apps"
    title = "Ứng dụng"
    icon = "view-app-grid-symbolic"

    def build(self) -> None:
        self._rows: list[Gtk.Widget] = []
        self._group = self.group(
            "Quy tắc theo ứng dụng",
            "Vietfox tự đổi chế độ khi bạn chuyển sang một ứng dụng. Tên ứng dụng khớp với tên lớp cửa sổ (WM_CLASS).",
        )
        add = Adw.ButtonRow(title="Thêm ứng dụng")
        add.set_start_icon_name("list-add-symbolic")
        add.connect("activated", lambda _row: self._add_rule())
        self._add_button = add
        self.track(add, "them ung dung app rule")
        self._reload()

    def _reload(self) -> None:
        for row in self._rows:
            self._group.remove(row)
        ids = {id(row) for row in self._rows}
        self.items = [item for item in self.items if id(item[0]) not in ids]
        self._rows = []

        rules = self.window.backend.get_rules()
        if not rules:
            empty = Adw.ActionRow(
                title="Chưa có quy tắc nào",
                subtitle="Mọi ứng dụng đang dùng chế độ gõ chung.",
            )
            empty.set_sensitive(False)
            self._group.add(empty)
            self._rows.append(empty)
            self.track(empty, "chua co quy tac ung dung")
        else:
            for index, rule in enumerate(rules):
                self._group.add(self._rule_row(index, rule))
        if self._add_button.get_parent():
            self._group.remove(self._add_button)
        self._group.add(self._add_button)

    def _rule_row(self, index: int, rule: dict[str, str]) -> Adw.ActionRow:
        app = rule.get("App", "")
        mode = str(rule.get("Mode", "2"))
        row = Adw.ActionRow(title=app)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_valign(Gtk.Align.CENTER)
        dropdown = Gtk.DropDown.new_from_strings([label for _, label in RULE_MODES])
        dropdown.set_valign(Gtk.Align.CENTER)
        selected = next((i for i, (value, _) in enumerate(RULE_MODES) if value == mode), 0)
        dropdown.set_selected(selected)
        box.append(dropdown)

        remove = Gtk.Button(icon_name="user-trash-symbolic")
        remove.add_css_class("flat")
        remove.set_valign(Gtk.Align.CENTER)
        remove.set_tooltip_text("Xoá quy tắc")
        remove.connect("clicked", lambda _button, i=index: self._delete_rule(i))
        box.append(remove)
        row.add_suffix(box)

        guard = {"on": False}

        def on_mode(_dropdown, _pspec) -> None:
            if guard["on"]:
                return
            rules = self.window.backend.get_rules()
            if not (0 <= index < len(rules)):
                return
            chosen = dropdown.get_selected()
            value = RULE_MODES[chosen][0] if 0 <= chosen < len(RULE_MODES) else "2"
            old = str(rules[index].get("Mode", "2"))
            rules[index] = {"App": app, "Mode": value}
            try:
                self.window.backend.set_rules(rules)
            except BackendError as error:
                restore(old)
                self.window.show_error(str(error))
                return
            self.window.show_saved(
                f"quy tắc cho {app}",
                lambda: self._undo_mode(app, index, old),
            )

        def restore(value: str) -> None:
            guard["on"] = True
            pos = next((i for i, (v, _) in enumerate(RULE_MODES) if v == value), 0)
            dropdown.set_selected(pos)
            guard["on"] = False

        dropdown.connect("notify::selected", on_mode)
        self.track(row, f"ung dung app {app} che do {RULE_MODES[selected][1]}")
        return row

    def _undo_mode(self, app: str, index: int, old: str) -> None:
        rules = self.window.backend.get_rules()
        if 0 <= index < len(rules):
            rules[index] = {"App": app, "Mode": old}
            try:
                self.window.backend.set_rules(rules)
            except BackendError as error:
                self.window.show_error(str(error))
                return
        self._reload()
        self.window.show_undone(f"quy tắc cho {app}")

    def _add_rule(self) -> None:
        dialog = FormDialog(
            "Thêm ứng dụng",
            "Chọn chế độ Vietfox dùng khi cửa sổ của ứng dụng này đang được chọn.",
            [
                {
                    "name": "app",
                    "label": "Ứng dụng",
                    "placeholder": "zalo, telegram, code…",
                },
                {"name": "mode", "label": "Chế độ", "choices": RULE_MODES},
            ],
            "Thêm",
        )

        def submitted(_dialog, data) -> None:
            app = data["app"].strip()
            rules = self.window.backend.get_rules()
            existing = next(
                (i for i, item in enumerate(rules) if item.get("App", "").casefold() == app.casefold()),
                None,
            )
            if existing is not None:
                rules[existing] = {"App": app, "Mode": data["mode"]}
            else:
                rules.append({"App": app, "Mode": data["mode"]})
            try:
                self.window.backend.set_rules(rules)
            except BackendError as error:
                self.window.show_error(str(error))
                return
            self._reload()
            self.window.show_toast(f'Đã lưu quy tắc cho “{app}”.')

        dialog.connect("submitted", submitted)
        dialog.present(self.window)

    def _delete_rule(self, index: int) -> None:
        rules = self.window.backend.get_rules()
        if not (0 <= index < len(rules)):
            return
        app = rules[index].get("App", "")

        def confirmed() -> None:
            try:
                self.window.backend.set_rules(rules[:index] + rules[index + 1 :])
            except BackendError as error:
                self.window.show_error(str(error))
                return
            self._reload()
            self.window.show_toast(f'Đã xoá quy tắc cho “{app}”.')

        self.window.confirm(
            f'Xoá quy tắc cho “{app}”?',
            "Ứng dụng sẽ dùng chế độ gõ chung.",
            "Xoá",
            confirmed,
            destructive=True,
        )
