#!/usr/bin/env bash
set -euo pipefail

ENGINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$ENGINE_DIR/.." && pwd)"
. /etc/os-release
ARCH="$(dpkg --print-architecture)"
CODENAME="${VERSION_CODENAME:-}"

if [[ "${ID:-}" != "ubuntu" || "$CODENAME" != "resolute" || "$ARCH" != "amd64" ]]; then
    echo "Source engine chưa được xác nhận ngoài Ubuntu Resolute amd64." >&2
    exit 1
fi

BUILD_DIR="${VIETFOX_ENGINE_BUILD_DIR:-$ROOT_DIR/build/engine}"
STAGE_DIR="${VIETFOX_ENGINE_STAGE_DIR:-$ROOT_DIR/build/engine-stage}"
VARIANT_DIR="$ENGINE_DIR/variants/ubuntu/$CODENAME/$ARCH"

cmake -S "$ENGINE_DIR/source" -B "$BUILD_DIR" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr \
    -DCMAKE_INSTALL_LIBDIR=/usr/lib
cmake --build "$BUILD_DIR" --parallel
rm -rf "$STAGE_DIR"
DESTDIR="$STAGE_DIR" cmake --install "$BUILD_DIR"

install -D -m 644 "$STAGE_DIR/usr/lib/fcitx5/libvietfox.so" \
    "$VARIANT_DIR/libvietfox.so"
install -D -m 644 "$STAGE_DIR/usr/lib/fcitx5/libvietfoxmigrate.so" \
    "$VARIANT_DIR/libvietfoxmigrate.so"
install -D -m 644 "$STAGE_DIR/usr/share/fcitx5/addon/vietfox.conf" \
    "$ENGINE_DIR/share/fcitx5/addon/vietfox.conf"
install -D -m 644 "$STAGE_DIR/usr/share/fcitx5/addon/vietfoxmigrate.conf" \
    "$ENGINE_DIR/share/fcitx5/addon/vietfoxmigrate.conf"
install -D -m 644 "$STAGE_DIR/usr/share/fcitx5/inputmethod/vietfox.conf" \
    "$ENGINE_DIR/share/fcitx5/inputmethod/vietfox.conf"
install -D -m 644 "$STAGE_DIR/usr/share/locale/vi/LC_MESSAGES/fcitx5-vietfox.mo" \
    "$ENGINE_DIR/share/locale/vi/LC_MESSAGES/fcitx5-vietfox.mo"
rm -rf "$ENGINE_DIR/share/icons"
mkdir -p "$ENGINE_DIR/share/icons"
cp -a "$STAGE_DIR/usr/share/icons/." "$ENGINE_DIR/share/icons/"

SUMS_FILE="$ENGINE_DIR/variants/SHA256SUMS"
SUMS_TMP="$(mktemp)"
grep -vF "ubuntu/$CODENAME/$ARCH/libvietfox.so" "$SUMS_FILE" | \
    grep -vF "ubuntu/$CODENAME/$ARCH/libvietfoxmigrate.so" > "$SUMS_TMP" || true
(cd "$ENGINE_DIR/variants" && sha256sum \
    "ubuntu/$CODENAME/$ARCH/libvietfox.so" \
    "ubuntu/$CODENAME/$ARCH/libvietfoxmigrate.so") >> "$SUMS_TMP"
mv "$SUMS_TMP" "$SUMS_FILE"
echo "Built Vietfox engine variant: $CODENAME/$ARCH"
