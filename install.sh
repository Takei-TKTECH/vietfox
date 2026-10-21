#!/usr/bin/env bash
# Cài Vietfox (giao diện + tuỳ chọn engine Ngó Sen đi kèm).
#
#   ./install.sh                     chỉ cài giao diện vào ~/.local
#   ./install.sh --with-engine       cài thêm engine vào /usr (cần sudo)
#   ./install.sh --with-engine --force-engine
#                                    ghi đè engine kể cả khi đã có gói fcitx5-ngosen
#   sudo ./install.sh --system       cài giao diện vào /usr/local
#   ./install.sh --uninstall         gỡ giao diện (thêm --with-engine để gỡ engine)
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${PREFIX:-$HOME/.local}"
WITH_ENGINE=0
FORCE_ENGINE=0
UNINSTALL=0

usage() {
    sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --system)
            PREFIX="/usr/local"
            ;;
        --with-engine)
            WITH_ENGINE=1
            ;;
        --force-engine)
            WITH_ENGINE=1
            FORCE_ENGINE=1
            ;;
        --uninstall)
            UNINSTALL=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Tham số không hợp lệ: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
    shift
done

DATA_DIR="$PREFIX/share/vietfox"
BIN_DIR="$PREFIX/bin"
APPS_DIR="$PREFIX/share/applications"
ICON_DIR="$PREFIX/share/icons/hicolor/scalable/apps"
DESKTOP="$APPS_DIR/io.github.vietfox.Vietfox.desktop"
ICON="$ICON_DIR/io.github.vietfox.Vietfox.svg"
SETTINGS_ICON="$ICON_DIR/io.github.vietfox.Settings.svg"
LAUNCHER="$BIN_DIR/vietfox"
DOC_DIR="$PREFIX/share/doc/vietfox"

SUDO=""
if [[ "$(id -u)" -ne 0 ]]; then
    SUDO="sudo"
fi

USER_HOME="$HOME"
if [[ -n "${SUDO_USER:-}" ]]; then
    USER_HOME="$(getent passwd "$SUDO_USER" | cut -d: -f6)"
fi
FORWARD_KEYS_UUID="forward-keys@ngosen.github.io"
FORWARD_KEYS_DIR="$USER_HOME/.local/share/gnome-shell/extensions/$FORWARD_KEYS_UUID"

if [[ $UNINSTALL -eq 1 ]]; then
    if [[ -f "$FORWARD_KEYS_DIR/.vietfox-managed" ]]; then
        gnome-extensions disable "$FORWARD_KEYS_UUID" >/dev/null 2>&1 || true
        rm -rf "$FORWARD_KEYS_DIR"
    fi
    SETTINGS_LAUNCHER="/usr/bin/fcitx5-ngosen-settings"
    $SUDO rm -f /usr/share/icons/hicolor/scalable/apps/io.github.vietfox.Settings.svg
    $SUDO rm -f /usr/share/icons/hicolor/scalable/apps/io.github.vietfox.Menu.*.svg
    $SUDO rm -f /usr/share/icons/hicolor/scalable/actions/vietfox-*.svg
    $SUDO gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
    if [[ -f "$SETTINGS_LAUNCHER" ]] && grep -q '^# Managed by Vietfox installer$' "$SETTINGS_LAUNCHER"; then
        $SUDO rm -f "$SETTINGS_LAUNCHER"
        echo "Đã gỡ launcher Settings của Vietfox."
    fi
    rm -rf "$DATA_DIR"
    rm -f "$LAUNCHER" "$DESKTOP" "$ICON" "$SETTINGS_ICON"
    command -v update-desktop-database >/dev/null && update-desktop-database "$APPS_DIR" || true
    if [[ $WITH_ENGINE -eq 1 ]]; then
        if dpkg -s fcitx5-ngosen >/dev/null 2>&1; then
            echo "Gói fcitx5-ngosen vẫn đang cài — không xoá engine để tránh hỏng bộ gõ."
        else
            ARCH_TRIPLET=""
            case "$(uname -m)" in
                x86_64) ARCH_TRIPLET="x86_64-linux-gnu" ;;
                aarch64) ARCH_TRIPLET="aarch64-linux-gnu" ;;
            esac
            if [[ -n "$ARCH_TRIPLET" ]]; then
                $SUDO rm -f "/usr/lib/$ARCH_TRIPLET/fcitx5/libngosen.so" \
                    "/usr/lib/$ARCH_TRIPLET/fcitx5/libngosenmigrate.so" \
                    /usr/share/fcitx5/addon/ngosen.conf \
                    /usr/share/fcitx5/addon/ngosenmigrate.conf \
                    /usr/share/fcitx5/inputmethod/ngosen.conf \
                    /usr/share/fcitx5/ngosen/vietnamese.cm.dict \
                    /usr/share/locale/vi/LC_MESSAGES/fcitx5-ngosen.mo
                echo "Đã gỡ engine đi kèm."
            fi
        fi
    fi
    echo "Đã gỡ Vietfox khỏi $PREFIX."
    echo "Cấu hình người dùng vẫn còn trong ~/.config/vietfox và fcitx5."
    exit 0
fi

if ! python3 - <<'PY'
import sys
try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Gtk, Adw
except Exception as error:
    print(f"Thiếu thư viện: {error}", file=sys.stderr)
    sys.exit(1)
PY
then
    echo "Cần PyGObject, GTK 4 và libadwaita 1."
    echo "Ubuntu/Debian: sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1"
    echo "Fedora:        sudo dnf install python3-gobject gtk4 libadwaita"
    echo "Arch:          sudo pacman -S python-gobject gtk4 libadwaita"
    exit 1
fi

# ---------------------------------------------------------------- giao diện
install -d "$DATA_DIR" "$BIN_DIR" "$APPS_DIR" "$ICON_DIR" "$DOC_DIR"
rm -rf "$DATA_DIR/vietfox" "$DATA_DIR/data"
cp -r "$SRC_DIR/vietfox" "$DATA_DIR/vietfox"
cp -r "$SRC_DIR/data" "$DATA_DIR/data"
find "$DATA_DIR" -name '__pycache__' -type d -prune -exec rm -rf {} +
cp "$SRC_DIR/data/io.github.vietfox.Vietfox.svg" "$ICON"
cp "$SRC_DIR/data/io.github.vietfox.Settings.svg" "$SETTINGS_ICON"
sed "s|^Exec=.*|Exec=$LAUNCHER|" \
    "$SRC_DIR/data/io.github.vietfox.Vietfox.desktop" > "$DESKTOP"

# GNOME 50.0–50.3 drops forwarded input-method keys in some applications,
# including Chrome. Ngó Sen ships this GNOME Shell compatibility extension.
if command -v gnome-shell >/dev/null 2>&1 &&
   gnome-shell --version 2>/dev/null | grep -Eq 'GNOME Shell 50\.'; then
    install -d "$FORWARD_KEYS_DIR"
    install -m 644 "$SRC_DIR/gnome-shell/$FORWARD_KEYS_UUID/extension.js" \
        "$FORWARD_KEYS_DIR/extension.js"
    install -m 644 "$SRC_DIR/gnome-shell/$FORWARD_KEYS_UUID/metadata.json" \
        "$FORWARD_KEYS_DIR/metadata.json"
    touch "$FORWARD_KEYS_DIR/.vietfox-managed"
    echo "Đã cài phần sửa lỗi gõ cho GNOME 50. Hãy đăng xuất/đăng nhập, rồi chạy: gnome-extensions enable $FORWARD_KEYS_UUID"
fi

cat > "$LAUNCHER" <<EOF
#!/bin/sh
export PYTHONPATH="$DATA_DIR\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 -m vietfox "\$@"
EOF
chmod +x "$LAUNCHER"
cp "$SRC_DIR/LICENSE" "$DOC_DIR/LICENSE"
[[ -f "$SRC_DIR/engine/COPYRIGHT" ]] && cp "$SRC_DIR/engine/COPYRIGHT" "$DOC_DIR/engine-COPYRIGHT"

# ------------------------------------------------------------------- engine
install_settings_launcher() {
    local settings_launcher="/usr/bin/fcitx5-ngosen-settings"
    $SUDO install -D -m 644 "$SRC_DIR/data/io.github.vietfox.Settings.svg" \
        /usr/share/icons/hicolor/scalable/apps/io.github.vietfox.Settings.svg
    # Fcitx action icons are looked up in the icon theme's Actions context.
    # The previous Apps-context location caused GTK to show a missing-icon glyph.
    $SUDO rm -f /usr/share/icons/hicolor/scalable/apps/io.github.vietfox.Menu.*.svg
    local menu_icon
    for menu_icon in "$SRC_DIR"/data/menu-icons/vietfox-*.svg; do
        $SUDO install -D -m 644 "$menu_icon" \
            "/usr/share/icons/hicolor/scalable/actions/$(basename "$menu_icon")"
    done
    $SUDO gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
    if [[ -e "$settings_launcher" ]] && ! grep -q '^# Managed by Vietfox installer$' "$settings_launcher"; then
        echo "Giữ nguyên $settings_launcher hiện có; không ghi đè Settings của Ngó Sen."
        return 0
    fi

    local quoted_launcher launcher_script
    printf -v quoted_launcher '%q' "$LAUNCHER"
    launcher_script=$(mktemp)
    cat > "$launcher_script" <<EOF
#!/bin/sh
# Managed by Vietfox installer
user_launcher="\${HOME}/.local/bin/vietfox"
if [ -x "\$user_launcher" ]; then
    exec "\$user_launcher" "\$@"
fi
exec $quoted_launcher "\$@"
EOF
    $SUDO install -m 755 "$launcher_script" "$settings_launcher"
    rm -f "$launcher_script"
    echo "Đã nối Settings trên top bar với Vietfox."
}

install_engine() {
    local arch_triplet libdir sharedir distro_id codename package_arch variant_dir
    . /etc/os-release
    distro_id="${ID:-}"
    codename="${VERSION_CODENAME:-}"
    if [[ "$distro_id" != "ubuntu" ]]; then
        echo "Engine đóng gói hiện chỉ hỗ trợ Ubuntu." >&2
        return 1
    fi
    if ! command -v dpkg >/dev/null; then
        echo "Không xác định được kiến trúc gói Ubuntu." >&2
        return 1
    fi
    package_arch="$(dpkg --print-architecture)"
    case "$package_arch" in
        amd64) arch_triplet="x86_64-linux-gnu" ;;
        arm64) arch_triplet="aarch64-linux-gnu" ;;
        *)
            echo "Engine Ubuntu chưa được đóng gói cho kiến trúc $package_arch." >&2
            return 1
            ;;
    esac
    variant_dir="$SRC_DIR/engine/variants/ubuntu/$codename/$package_arch"
    if [[ ! -f "$variant_dir/libngosen.so" || ! -f "$variant_dir/libngosenmigrate.so" ]]; then
        echo "Chưa có engine Vietfox cho Ubuntu $codename ($package_arch)." >&2
        return 1
    fi
    libdir="/usr/lib/$arch_triplet/fcitx5"
    sharedir="/usr/share/fcitx5"

    echo "Cài engine Vietfox cho Ubuntu $codename ($package_arch) vào $libdir…"
    $SUDO install -d "$libdir" "$sharedir/addon" "$sharedir/inputmethod" "$sharedir/ngosen"
    $SUDO install -m 644 "$variant_dir/libngosen.so" \
        "$variant_dir/libngosenmigrate.so" "$libdir/"
    $SUDO install -m 644 "$SRC_DIR/engine/share/fcitx5/addon/ngosen.conf" \
        "$SRC_DIR/engine/share/fcitx5/addon/ngosenmigrate.conf" "$sharedir/addon/"
    $SUDO install -m 644 "$SRC_DIR/engine/share/fcitx5/inputmethod/ngosen.conf" "$sharedir/inputmethod/"
    $SUDO install -m 644 "$SRC_DIR/engine/share/fcitx5/ngosen/vietnamese.cm.dict" "$sharedir/ngosen/"
    $SUDO install -D -m 644 "$SRC_DIR/engine/share/locale/vi/LC_MESSAGES/fcitx5-ngosen.mo" \
        /usr/share/locale/vi/LC_MESSAGES/fcitx5-ngosen.mo

    if ldd "$libdir/libngosen.so" 2>/dev/null | grep -q "not found"; then
        echo "Cảnh báo: engine thiếu thư viện:" >&2
        ldd "$libdir/libngosen.so" | grep "not found" >&2
    fi

    # The bundled engine starts a fixed path for its top-bar Settings action.
    # Preserve any upstream launcher already installed at that path.
    install_settings_launcher
}

if [[ $WITH_ENGINE -eq 1 ]]; then
    if dpkg -s fcitx5-ngosen >/dev/null 2>&1 && [[ $FORCE_ENGINE -eq 0 ]]; then
        echo "Đã có gói fcitx5-ngosen — dùng engine hệ thống, bỏ qua bản đi kèm."
        echo "(Dùng --force-engine nếu vẫn muốn ghi đè.)"
        install_settings_launcher
    else
        install_engine
    fi
elif dpkg -s fcitx5-ngosen >/dev/null 2>&1 || [[ -f "/usr/lib/$(uname -m)-linux-gnu/fcitx5/libngosen.so" ]]; then
    install_settings_launcher
else
    echo
    echo "Lưu ý: chưa có engine Vietfox. Muốn cài kèm, chạy lại với --with-engine."
fi

# ------------------------------------------------- thêm vào nhóm gõ fcitx5
enable_input_method() {
    local profile="$HOME/.config/fcitx5/profile"
    if [[ ! -f "$profile" ]]; then
        echo "Chưa có $profile — mở fcitx5 một lần rồi thêm “Vietfox” trong Cấu hình bàn phím."
        return 0
    fi
    python3 - "$profile" <<'PY'
import re
import sys

path = sys.argv[1]
text = open(path, encoding="utf-8").read()
if re.search(r"^Name=ngosen$", text, re.M):
    print("Vietfox đã có trong nhóm gõ của fcitx5.")
    raise SystemExit(0)

lines = text.splitlines()
start = next((i for i, line in enumerate(lines) if line.strip() == "[Groups/0]"), None)
if start is None:
    print("Không thấy nhóm [Groups/0]; hãy thêm Vietfox bằng fcitx5-configtool.", file=sys.stderr)
    raise SystemExit(1)

end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("[")), len(lines))
indices = [int(m.group(1)) for line in lines[start:end]
           if (m := re.match(r"\[Groups/0/Items/(\d+)\]", line.strip()))]
new_index = max(indices, default=-1) + 1

has_default = any(re.match(r"DefaultIM=.+", line) for line in lines[start:end])
if not has_default:
    insert_at = start + 1
    while insert_at < end and lines[insert_at].startswith("#"):
        insert_at += 1
    lines.insert(insert_at, "DefaultIM=ngosen")
    end += 1

lines[end:end] = [f"[Groups/0/Items/{new_index}]", "Name=ngosen", "Layout="]
open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("Đã thêm Vietfox vào nhóm gõ của fcitx5.")
PY
}

PROFILE="$HOME/.config/fcitx5/profile"
if command -v fcitx5 >/dev/null && [[ -f "/usr/share/fcitx5/addon/ngosen.conf" ]] && [[ -f "$PROFILE" ]]; then
    BEFORE_HASH="$(sha256sum "$PROFILE" | cut -d' ' -f1)"
    enable_input_method
    AFTER_HASH="$(sha256sum "$PROFILE" | cut -d' ' -f1)"
    if [[ "$BEFORE_HASH" != "$AFTER_HASH" ]] && pgrep -x fcitx5 >/dev/null; then
        fcitx5-remote -e >/dev/null 2>&1 || true
        sleep 1
        if [[ -n "${WAYLAND_DISPLAY:-}${DISPLAY:-}" ]]; then
            setsid fcitx5 -d >/dev/null 2>&1 || true
        fi
    fi
fi

# ------------------------------------------------------------------- duong dan
if command -v update-desktop-database >/dev/null; then
    update-desktop-database "$APPS_DIR" || true
fi
if command -v gtk-update-icon-cache >/dev/null; then
    gtk-update-icon-cache -f -t "$PREFIX/share/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "Đã cài Vietfox vào $PREFIX."
echo "Chạy: $LAUNCHER"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "Thêm $BIN_DIR vào PATH để gõ 'vietfox' từ terminal."
fi
