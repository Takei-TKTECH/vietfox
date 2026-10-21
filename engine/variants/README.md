# Engine theo Ubuntu và kiến trúc

Installer chỉ cài engine khi có đủ thư viện Vietfox đã build cho đúng codename Ubuntu và kiến trúc.
Binary Ngó Sen cũ không được dùng làm phương án dự phòng vì chúng đăng ký addon khác.

| Ubuntu | Kiến trúc | Trạng thái |
| --- | --- | --- |
| 26.04 (resolute) | amd64 | Vietfox engine, build từ `source/` trên Ubuntu 26.04 |
| Ubuntu khác / arm64 | — | Chưa có bản build được xác nhận; installer dừng thay vì cài binary Ngó Sen |

Mỗi biến thể cần cả `libvietfox.so` và `libvietfoxmigrate.so`. Chỉ thêm biến thể sau khi build
trên Ubuntu tương ứng, kiểm tra phụ thuộc động và thử nâng cấp cấu hình Fcitx5 cũ.
