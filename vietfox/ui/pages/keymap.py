# SPDX-License-Identifier: GPL-3.0-or-later
"""Editor for Vietfox's custom keymap subconfiguration."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from ...core.backend import BackendError
from ..dialogs import FormDialog
from .base import Page

ACTIONS = [
    ("XoaDauThanh", "Xóa dấu thanh"),
    ("DauSac", "Dấu sắc"),
    ("DauHuyen", "Dấu huyền"),
    ("DauHoi", "Dấu hỏi"),
    ("DauNga", "Dấu ngã"),
    ("DauNang", "Dấu nặng"),
    ("A_Â", "a → â"),
    ("E_Ê", "e → ê"),
    ("O_Ô", "o → ô"),
    ("AEO_ÂÊÔ", "a/e/o → â/ê/ô"),
    ("UOA_ƯƠĂ", "u/o/a → ư/ơ/ă"),
    ("D_Đ", "d → đ"),
    ("UO_ƯƠ", "u/o → ư/ơ"),
    ("A_Ă", "a → ă"),
    ("__ă", "ă"),
    ("_Ă", "Ă"),
    ("__â", "â"),
    ("_Â", "Â"),
    ("__ê", "ê"),
    ("_Ê", "Ê"),
    ("__ô", "ô"),
    ("_Ô", "Ô"),
    ("__ư", "ư"),
    ("_Ư", "Ư"),
    ("__ơ", "ơ"),
    ("_Ơ", "Ơ"),
    ("__đ", "đ"),
    ("_Đ", "Đ"),
    ("UOA_ƯƠĂ__Ư", "u/o/a → ư/ơ/ă; ư"),
]
ACTION_LABELS = dict(ACTIONS)

PRESETS = {
    "Telex": [("z", "XoaDauThanh"), ("s", "DauSac"), ("f", "DauHuyen"), ("r", "DauHoi"), ("x", "DauNga"), ("j", "DauNang"), ("a", "A_Â"), ("e", "E_Ê"), ("o", "O_Ô"), ("w", "UOA_ƯƠĂ"), ("d", "D_Đ")],
    "VNI": [("0", "XoaDauThanh"), ("1", "DauSac"), ("2", "DauHuyen"), ("3", "DauHoi"), ("4", "DauNga"), ("5", "DauNang"), ("6", "AEO_ÂÊÔ"), ("7", "UO_ƯƠ"), ("8", "A_Ă"), ("9", "D_Đ")],
    "VIQR": [("0", "XoaDauThanh"), ("'", "DauSac"), ("`", "DauHuyen"), ("?", "DauHoi"), ("~", "DauNga"), (".", "DauNang"), ("^", "AEO_ÂÊÔ"), ("+", "UO_ƯƠ"), ("*", "UO_ƯƠ"), ("(", "A_Ă"), ("d", "D_Đ")],
    "Telex + VNI": [("z", "XoaDauThanh"), ("s", "DauSac"), ("f", "DauHuyen"), ("r", "DauHoi"), ("x", "DauNga"), ("j", "DauNang"), ("a", "A_Â"), ("e", "E_Ê"), ("o", "O_Ô"), ("w", "UOA_ƯƠĂ"), ("d", "D_Đ"), ("0", "XoaDauThanh"), ("1", "DauSac"), ("2", "DauHuyen"), ("3", "DauHoi"), ("4", "DauNga"), ("5", "DauNang"), ("6", "AEO_ÂÊÔ"), ("7", "UO_ƯƠ"), ("8", "A_Ă"), ("9", "D_Đ")],
    "Telex + VNI + VIQR": [("z", "XoaDauThanh"), ("s", "DauSac"), ("f", "DauHuyen"), ("r", "DauHoi"), ("x", "DauNga"), ("j", "DauNang"), ("a", "A_Â"), ("e", "E_Ê"), ("o", "O_Ô"), ("w", "UOA_ƯƠĂ"), ("d", "D_Đ"), ("0", "XoaDauThanh"), ("1", "DauSac"), ("2", "DauHuyen"), ("3", "DauHoi"), ("4", "DauNga"), ("5", "DauNang"), ("6", "AEO_ÂÊÔ"), ("7", "UO_ƯƠ"), ("8", "A_Ă"), ("9", "D_Đ"), ("'", "DauSac"), ("`", "DauHuyen"), ("?", "DauHoi"), ("~", "DauNga"), (".", "DauNang"), ("^", "AEO_ÂÊÔ"), ("+", "UO_ƯƠ"), ("*", "UO_ƯƠ"), ("(", "A_Ă"), ("\\", "D_Đ")],
    "VNI Bàn phím tiếng Pháp": [("&", "XoaDauThanh"), ("é", "DauSac"), ('"', "DauHuyen"), ("'", "DauHoi"), ("(", "DauNga"), ("-", "DauNang"), ("è", "AEO_ÂÊÔ"), ("_", "UO_ƯƠ"), ("ç", "A_Ă"), ("à", "D_Đ")],
    "Microsoft layout": [("8", "DauSac"), ("5", "DauHuyen"), ("6", "DauHoi"), ("7", "DauNga"), ("9", "DauNang"), ("1", "__ă"), ("!", "_Ă"), ("2", "__â"), ("@", "_Â"), ("3", "__ê"), ("#", "_Ê"), ("4", "__ô"), ("$", "_Ô"), ("0", "__đ"), (")", "_Đ")],
    "Telex W": [("z", "XoaDauThanh"), ("s", "DauSac"), ("f", "DauHuyen"), ("r", "DauHoi"), ("x", "DauNga"), ("j", "DauNang"), ("a", "A_Â"), ("e", "E_Ê"), ("o", "O_Ô"), ("w", "UOA_ƯƠĂ__Ư"), ("d", "D_Đ")],
}


class KeymapPage(Page):
    ident = "keymap"
    title = "Keymap"
    icon = "preferences-desktop-keyboard-shortcuts-symbolic"

    def build(self) -> None:
        settings = self.group(
            "Keymap tuỳ chỉnh",
            "Gán một phím cho thao tác xử lý tiếng Việt. Bật keymap để các ánh xạ bên dưới có hiệu lực.",
        )
        self.add(
            settings,
            self.switch(
                "EnableCustomKeymap",
                "Bật keymap tuỳ chỉnh",
                "Các ánh xạ này được áp dụng trong engine Vietfox.",
                False,
                keywords="keymap ban phim tuy chinh",
            ),
        )
        self._group = self.group("Ánh xạ phím")
        presets = Adw.ActionRow(title="Bộ quy tắc có sẵn")
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._preset = Gtk.DropDown.new_from_strings(list(PRESETS))
        self._preset.set_valign(Gtk.Align.CENTER)
        apply = Gtk.Button(label="Áp dụng")
        apply.add_css_class("flat")
        apply.set_valign(Gtk.Align.CENTER)
        apply.connect("clicked", self._apply_preset)
        box.append(self._preset)
        box.append(apply)
        presets.add_suffix(box)
        self._group.add(presets)
        self.track(presets, "telex vni viqr microsoft preset bo quy tac")

        self._rows: list[Gtk.Widget] = []
        self._reload()
        add = Adw.ButtonRow(title="Thêm ánh xạ phím")
        add.set_start_icon_name("list-add-symbolic")
        add.connect("activated", lambda _row: self._edit(None))
        self._add_button = add
        self._group.add(add)
        self.track(add, "them keymap anh xa phim")

    def _reload(self) -> None:
        previous_rows = getattr(self, "_rows", [])
        row_ids = {id(row) for row in previous_rows}
        self.items = [item for item in self.items if id(item[0]) not in row_ids]
        for row in previous_rows:
            self._group.remove(row)
        self._rows = []
        for index, item in enumerate(self.window.backend.get_keymap()):
            key = item.get("Key", "")
            action = item.get("Value", "")
            row = Adw.ActionRow(title=key, subtitle=ACTION_LABELS.get(action, action))
            row.set_activatable(True)
            row.connect("activated", lambda _row, i=index: self._edit(i))
            remove = Gtk.Button(icon_name="user-trash-symbolic")
            remove.add_css_class("flat")
            remove.set_valign(Gtk.Align.CENTER)
            remove.set_tooltip_text("Xoá ánh xạ")
            remove.connect("clicked", lambda _button, i=index: self._remove(i))
            row.add_suffix(remove)
            self._group.add(row)
            self._rows.append(row)
            self.track(row, f"keymap {key} {action}")
        if not self._rows:
            empty = Adw.ActionRow(title="Chưa có ánh xạ tuỳ chỉnh")
            empty.set_sensitive(False)
            self._group.add(empty)
            self._rows.append(empty)

    def _save(self, rows: list[dict[str, str]], title: str) -> None:
        old = self.window.backend.get_keymap()
        try:
            self.window.backend.set_keymap(rows)
        except BackendError as error:
            self.window.show_error(str(error))
            return
        self._reload()
        self.window.show_saved(title, lambda: self._undo(old, title))

    def _undo(self, rows: list[dict[str, str]], title: str) -> None:
        try:
            self.window.backend.set_keymap(rows)
        except BackendError as error:
            self.window.show_error(str(error))
            return
        self._reload()
        self.window.show_undone(title)

    def _edit(self, index: int | None) -> None:
        rows = self.window.backend.get_keymap()
        current = rows[index] if index is not None and index < len(rows) else {"Key": "", "Value": ACTIONS[0][0]}
        choices = list(ACTIONS)
        if current.get("Value") not in ACTION_LABELS:
            choices.append((current["Value"], current["Value"]))
        dialog = FormDialog(
            "Sửa ánh xạ phím" if index is not None else "Thêm ánh xạ phím",
            "Mỗi phím chỉ có một thao tác. Lưu trữ trực tiếp vào cấu hình Vietfox.",
            [
                {"name": "key", "label": "Phím", "placeholder": "Ví dụ: w", "value": current.get("Key", "")},
                {"name": "action", "label": "Thao tác", "choices": choices, "value": current.get("Value")},
            ],
            "Lưu",
        )

        def submitted(_dialog, data) -> None:
            key = data["key"].strip()
            if len(key) != 1:
                self.window.show_error("Phím ánh xạ phải là một ký tự.")
                return
            target = index if index is not None and index < len(rows) else next(
                (i for i, item in enumerate(rows) if item.get("Key") == key), None
            )
            entry = {"Key": key, "Value": data["action"]}
            if target is None:
                rows.append(entry)
            else:
                rows[target] = entry
            self._save(rows, f"ánh xạ phím {key}")

        dialog.connect("submitted", submitted)
        dialog.present(self.window)

    def _remove(self, index: int) -> None:
        rows = self.window.backend.get_keymap()
        if 0 <= index < len(rows):
            removed = rows.pop(index)
            self._save(rows, f"ánh xạ phím {removed.get('Key', '')}")

    def _apply_preset(self, _button) -> None:
        names = list(PRESETS)
        index = self._preset.get_selected()
        if 0 <= index < len(names):
            name = names[index]
            self._save([{"Key": key, "Value": action} for key, action in PRESETS[name]], f"keymap {name}")
