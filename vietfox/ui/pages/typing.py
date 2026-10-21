# SPDX-License-Identifier: GPL-3.0-or-later
"""The typing page: how Vietnamese is composed."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from ..pages.base import Page

INPUT_METHODS = [
    ("Telex", "Telex"),
    ("VNI", "VNI"),
    ("Telex + VNI", "Telex + VNI"),
    ("Telex + VNI + VIQR", "Telex + VNI + VIQR"),
    ("VIQR", "VIQR"),
    ("Microsoft layout", "Kiểu Microsoft"),
    ("VNI Bàn phím tiếng Pháp", "VNI bàn phím tiếng Pháp"),
    ("Custom", "Tuỳ chỉnh"),
]

CHARSETS = [
    ("Unicode", "Unicode"),
    ("Unicode tổ hợp", "Unicode tổ hợp"),
    ("UTF-8", "UTF-8"),
    ("TCVN3 (ABC)", "TCVN3 (ABC)"),
    ("VNI Windows", "VNI Windows"),
    ("VISCII", "VISCII"),
    ("VIQR", "VIQR"),
    ("VPS", "VPS"),
    ("BKHCM 1", "BKHCM 1"),
    ("BKHCM 2", "BKHCM 2"),
    ("Vietware Full", "Vietware Full"),
    ("Vietware X", "Vietware X"),
    ("Windows 1258 codepage", "Windows 1258"),
    ("NCR Decimal", "NCR thập phân"),
    ("NCR Hex", "NCR thập lục phân"),
    ("Unicode C string Decimal", "Unicode C (thập phân)"),
    ("Unicode C string Hex", "Unicode C (thập lục phân)"),
]

W2U = [
    ("Disabled", "Tắt"),
    ("Non-Start", "Không phải đầu từ"),
    ("Everywhere", "Mọi nơi"),
]


class TypingPage(Page):
    ident = "typing"
    title = "Gõ chữ"
    icon = "input-keyboard-symbolic"

    def build(self) -> None:
        modes = self.group(
            "Chế độ gõ",
            "Mặc định đưa chữ thẳng vào ứng dụng và là chế độ nên dùng. Gạch chân hiện chữ đang gõ dưới con trỏ.",
        )
        self.add(
            modes,
            self.combo(
                "Mode",
                "Chế độ gõ",
                [("Sen", "Mặc định"), ("Preedit", "Gạch chân"), ("Emoji Picker", "Chọn emoji"), ("OFF", "Tắt")],
                default="Sen",
                keywords="mode sen preedit gach chan emoji tat kieu go",
            ),
        )
        self.add(
            modes,
            self.combo(
                "InputMethod",
                "Kiểu gõ",
                INPUT_METHODS,
                default="Telex",
                keywords="telex vni viqr kieu go",
            ),
        )
        self.add(
            modes,
            self.combo(
                "OutputCharset",
                "Bảng mã",
                CHARSETS,
                default="Unicode",
                keywords="bang ma charset unicode tcvn viscii vni",
            ),
        )

        example = Adw.ActionRow(
            title="Ví dụ",
            subtitle="Chữ hiện ngay trong ô nhập, không có gạch chân.",
        )
        sample = Gtk.Label(label="vieetj → việt")
        sample.add_css_class("vf-mono")
        sample.add_css_class("dim-label")
        example.add_suffix(sample)
        self.add(modes, example, "vi du go sen go tay")

        spelling = self.group("Cách bỏ dấu")
        self.add(
            spelling,
            self.switch(
                "SpellCheck",
                "Kiểm tra chính tả",
                "Dùng từ điển để nhận ra từ không hợp lệ.",
                True,
                keywords="chinh ta spell check tu dien",
            ),
        )
        self.add(
            spelling,
            self.switch(
                "AutoNonVnRestore",
                "Tự khôi phục từ gõ sai",
                "Từ không hợp lệ được trả lại đúng như đã gõ.",
                True,
                keywords="khoi phuc tu go sai restore",
            ),
        )
        self.add(
            spelling,
            self.switch(
                "ModernStyle",
                "Bỏ dấu kiểu mới",
                "oà, uý thay vì òa, úy.",
                True,
                keywords="dau kieu moi oa uy",
            ),
        )
        self.add(
            spelling,
            self.switch(
                "FreeMarking",
                "Gõ tự do",
                "Cho phép đặt dấu ở nhiều vị trí hơn khi gõ.",
                True,
                keywords="go tu do free marking",
            ),
        )
        self.add(
            spelling,
            self.switch(
                "DdFreeStyle",
                "Vẫn gõ dd ra đ",
                "Khi tự khôi phục từ gõ sai vẫn bật.",
                True,
                keywords="dd d",
            ),
        )
        self.add(
            spelling,
            self.switch(
                "BackspaceRemovesTone",
                "Backspace xóa dấu thanh",
                "Xoá dấu trước khi xoá chữ.",
                False,
                keywords="backspace xoa dau thanh",
            ),
        )

        speed = self.group("Gõ nhanh")
        self.add(
            speed,
            self.combo(
                "W2U",
                "Gõ w ra ư",
                W2U,
                default="Non-Start",
                keywords="w u",
            ),
        )
        self.add(
            speed,
            self.combo(
                "BracketTransform",
                "Phím [ ] ra ơ ư",
                W2U,
                default="Disabled",
                keywords="ngoac vuong o u",
            ),
        )
        self.add(
            speed,
            self.switch(
                "DoubleSpaceToPeriod",
                "Hai dấu cách thành dấu chấm",
                False,
                keywords="hai dau cach dau cham",
            ),
        )
        self.add(
            speed,
            self.switch(
                "DoubleHyphenToEmDash",
                "Hai gạch nối thành gạch dài",
                False,
                keywords="gach noi gach dai em dash",
            ),
        )
        self.add(
            speed,
            self.switch(
                "AutoCapitalizeAfterPunctuation",
                "Tự viết hoa sau dấu câu",
                "Sau dấu chấm, chấm than, chấm hỏi hoặc Enter.",
                False,
                keywords="viet hoa dau cau",
            ),
        )

        advanced = self.group(
            "Nâng cao",
            "Các tuỳ chọn này thay đổi cách Vietfox chờ ứng dụng nhận chữ. Chỉ đổi khi gặp lỗi gõ.",
        )
        self.add(
            advanced,
            self.switch(
                "useSurroundingTextIfPossible",
                "Dùng surrounding text khi có thể",
                False,
                keywords="surrounding text",
            ),
        )
        self.add(
            advanced,
            self.switch(
                "WaitSurroundingEvent",
                "Chờ sự kiện surrounding text",
                "Thử nghiệm, dùng cho chế độ Mặc định.",
                True,
                keywords="cho su kien surrounding",
            ),
        )
        self.add(
            advanced,
            self.switch(
                "MessengerSelectOvertype",
                "Chọn và gõ đè trong Messenger",
                "Thử nghiệm, dành cho ô soạn tin của Messenger.",
                True,
                keywords="messenger go de",
            ),
        )

        timings = Adw.ExpanderRow(
            title="Thời gian chờ",
            subtitle="Mili giây. Giá trị nhỏ hơn thì gõ nhanh hơn nhưng dễ sót chữ.",
        )
        for key, title, default, upper, subtitle in [
            ("WaitSurroundingTimeoutMs", "Chờ tối đa", 50, 1000, "Sau khi xoá chữ, chờ sự kiện surrounding text."),
            ("WaitSurroundingShortMs", "Chờ ngắn", 40, 1000, "Dùng sau hai lần chờ liên tiếp không có sự kiện."),
            ("WaitSurroundingProbeEvery", "Kiểm tra lại mỗi", 4, 100, "Số lần thay thế khi ảnh chụp của ứng dụng không đổi."),
            ("WaitSurroundingSettleMs", "Chờ ổn định", 40, 1000, "Chờ thêm sau khi xoá xong, chỉ trong Messenger."),
            ("WaitSurroundingSettleFirstWordMs", "Chờ từ đầu tiên", 60, 1000, "Ô soạn tin Messenger còn đang mở."),
            ("WaitSurroundingMinPerKeyMs", "Tối thiểu mỗi phím", 8, 200, ""),
            ("SurrDeleteSleepMs", "Nghỉ sau khi xoá", 4, 200, ""),
            ("SurrCommitSleepMs", "Nghỉ sau khi chèn", 3, 200, ""),
        ]:
            row = self.spin(key, title, default, lower=1, upper=upper, subtitle=subtitle)
            timings.add_row(row)
            self.track(row, "thoi gian cho timing mili giay")
        advanced.add(timings)
        self.track(timings, "thoi gian cho timing mili giay")
