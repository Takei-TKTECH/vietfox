# Engine đi kèm Vietfox

Thư mục này chứa engine gõ lấy từ dự án **Ngó Sen** để bộ cài Vietfox hoạt động
độc lập, không cần cài thêm gói `fcitx5-ngosen` của hệ thống.

| Thông tin | Giá trị |
| --- | --- |
| Nguồn | https://github.com/ngosen/ngosen |
| Phiên bản | 1.5.2-1 |
| Giấy phép | GPL-3.0-or-later (xem `COPYRIGHT`) |
| Hệ điều hành | Ubuntu 22.04, 24.04, 26.04 |
| Kiến trúc | amd64 (x86_64), arm64 (aarch64) |
| Yêu cầu | fcitx5 ≥ 5.1.19, libc ≥ 2.39 |

## File và vị trí cài

| Trong repo | Cài vào |
| --- | --- |
| `lib/libngosen.so` | `/usr/lib/<triplet>/fcitx5/` |
| `lib/libngosenmigrate.so` | `/usr/lib/<triplet>/fcitx5/` |
| `share/fcitx5/addon/ngosen.conf` | `/usr/share/fcitx5/addon/` |
| `share/fcitx5/addon/ngosenmigrate.conf` | `/usr/share/fcitx5/addon/` |
| `share/fcitx5/inputmethod/ngosen.conf` | `/usr/share/fcitx5/inputmethod/` |
| `share/fcitx5/ngosen/vietnamese.cm.dict` | `/usr/share/fcitx5/ngosen/` |

Engine mở Settings từ menu top bar bằng `/usr/bin/fcitx5-ngosen-settings`. `install.sh` cài launcher
tương thích trỏ tới giao diện Vietfox nếu đường dẫn này chưa có chương trình khác.

`patches/vietfox-status-menu.patch` đưa các thao tác nhanh trở lại menu (bảng mã, chính tả, gõ tắt, khôi phục từ, từ điển, nhật ký) và Việt hoá nhãn; mục mở giao diện là **Cài đặt Vietfox**. Trạng thái bật/tắt hiển thị bằng dấu ✓/✖, theo menu native của Fcitx.
`patches/vietfox-punctuation-fallback.patch` giữ nguyên chữ tiếng Việt khi người dùng gõ dấu câu
cuối từ. Từ `xêm` cũng được thêm vào từ điển để tránh khôi phục nhầm về phím Telex.
`install.sh --with-engine` chọn thư viện theo `VERSION_CODENAME` và kiến trúc gói Ubuntu.
Các engine jammy/noble và resolute arm64 lấy từ gói Ngó Sen 1.5.2-1 tương ứng;
resolute amd64 được rebuild từ cùng tag với patch menu Vietfox. Danh sách và nguồn nằm
tại `variants/README.md`. Catalog tiếng Việt nằm tại `share/locale/vi/LC_MESSAGES/`.

Icon Settings riêng nằm tại
`data/io.github.vietfox.Settings.svg`, được cài vào hicolor để hiển thị trắng trên nền tối.
Các biểu tượng thao tác nhanh cùng nét trắng được lưu trong `data/menu-icons/` và cài vào
ngữ cảnh `actions` của hicolor để Fcitx tìm thấy đúng icon.

Tên addon vẫn là `ngosen` để dùng chung định dạng cấu hình, từ điển và gõ tắt
với Ngó Sen. Giao diện Vietfox nhận addon này qua `ADDON_NAMES = ("ngosen", "vietfox")`.

## Lưu ý khi bảo trì

- `.so` phụ thuộc ABI của fcitx5. Ubuntu ngoài các bản đã liệt kê chưa được đóng gói.
- Chỉ engine resolute amd64 hiện đã được build với menu Vietfox và nhãn tiếng Việt; các gói Ubuntu còn lại vẫn là binary upstream, cần rebuild từ source tương ứng để có menu giống hệt.
- Không sửa trực tiếp file trong `engine/`; luôn chép từ gói/bản phát hành gốc
  và cập nhật bảng trên.
- Nếu máy đã cài `fcitx5-ngosen`, `install.sh` mặc định dùng engine hệ thống
  thay vì ghi đè. Dùng `--force-engine` để buộc ghi đè.
