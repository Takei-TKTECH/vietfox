# Hướng dẫn cho Codex — Vietfox

## Mục tiêu và kiến trúc

Vietfox là ứng dụng cấu hình bộ gõ tiếng Việt trên Ubuntu. UI viết bằng Python, GTK 4 và libadwaita; kết nối tới fcitx5 qua D-Bus. Addon Fcitx5 có ID `vietfox`, build từ source trong `engine/source/`, dùng lõi gõ Ngó Sen và giữ các đường dẫn cấu hình cũ để tương thích.

- `vietfox/application.py`: khởi tạo `Adw.Application`.
- `vietfox/core/backend.py`: giao tiếp D-Bus với fcitx5 và chế độ lưu cấu hình tạm khi offline.
- `vietfox/core/store.py`: mặc định, kiểu dữ liệu, đọc/ghi và hoàn tác cấu hình.
- `vietfox/ui/window.py`: cửa sổ chính, điều hướng, tìm kiếm, menu và thông báo.
- `vietfox/ui/pages/`: các trang cài đặt theo tính năng.
- `vietfox/ui/dialogs.py`, `vietfox/ui/helpers.py`: hộp thoại và hàm hỗ trợ UI.
- `data/`: desktop entry và icon.
- `engine/source/`: source engine từ Ngó Sen đã tách GUI và build thành addon Vietfox.
- `engine/variants/`: binary theo Ubuntu/kiến trúc.
- `install.sh`: cài/gỡ giao diện và tuỳ chọn cài engine.

## Quy ước phát triển

- Sửa mã nguồn trong repo này; không chỉnh bản cài ở `~/.local/share/vietfox`.
- Giữ giao diện và thông báo bằng tiếng Việt, theo phong cách GTK/libadwaita hiện có.
- Cài đặt UI cần đăng ký mặc định và kiểu dữ liệu trong store để lưu, hoàn tác, đặt lại và sao lưu hoạt động nhất quán.
- Thay đổi addon hoặc thư viện trong `engine/` có thể ảnh hưởng ABI fcitx5. Build source trước; chỉ cài engine sau khi kiểm tra ABI và đúng variant Ubuntu.
- `./install.sh` cập nhật bản cài giao diện. Cài engine vào `/usr` cần quyền root; không chạy các thao tác cài đặt hệ thống khi chưa được yêu cầu.
- Đường dẫn repo có dấu tiếng Việt và khoảng trắng; luôn quote đường dẫn trong lệnh shell.

## Lệnh dự án

- Chạy từ repo: `./run.sh` hoặc `python3 -m vietfox`.
- Cài giao diện: `./install.sh`.
- Cài kèm engine: `./install.sh --with-engine` (cần quyền root để chép engine vào `/usr`).
- Bộ kiểm tra có sẵn: `python3 -m unittest discover -s tests -v`.

## Lịch sử tại thời điểm tạo hướng dẫn

HEAD là `1f1dc22` (`Vietfox: nhãn 'Mặc định', tên tray/addon thành Vietfox`). Hãy kiểm tra `git status` và lịch sử mới nhất trước khi sửa để giữ nguyên thay đổi sẵn có.
