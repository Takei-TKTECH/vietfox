# Engine đi kèm Vietfox

Thư mục này chứa engine gõ lấy từ dự án **Ngó Sen** để bộ cài Vietfox hoạt động
độc lập, không cần cài thêm gói `fcitx5-ngosen` của hệ thống.

| Thông tin | Giá trị |
| --- | --- |
| Nguồn | https://github.com/ngosen/ngosen |
| Phiên bản | 1.5.4-2 |
| Giấy phép | GPL-3.0-or-later (xem `COPYRIGHT`) |
| Kiến trúc | amd64 (x86_64), aarch64 |
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

Tên addon vẫn là `ngosen` để dùng chung định dạng cấu hình, từ điển và gõ tắt
với Ngó Sen. Giao diện Vietfox nhận addon này qua `ADDON_NAMES = ("ngosen", "vietfox")`.

## Lưu ý khi bảo trì

- `.so` phụ thuộc ABI của fcitx5. Khi Ubuntu nâng fcitx5 lên phiên bản mới,
  cần lấy lại engine từ bản phát hành Ngó Sen tương ứng rồi cập nhật thư mục này.
- Không sửa trực tiếp file trong `engine/`; luôn chép từ gói/bản phát hành gốc
  và cập nhật bảng trên.
- Nếu máy đã cài `fcitx5-ngosen`, `install.sh` mặc định dùng engine hệ thống
  thay vì ghi đè. Dùng `--force-engine` để buộc ghi đè.
