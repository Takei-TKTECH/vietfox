# Ubuntu engine variants

These ABI-specific engine binaries come from Ngó Sen 1.5.2-1 Ubuntu packages.
The Ubuntu 26.04 amd64 variant is rebuilt from tag `ngosen-1.5.2-1` with
`../patches/vietfox-status-menu.patch`; all variants are selected by Ubuntu
codename and Debian architecture in `install.sh`. This patch restores the quick
feature actions and hardcodes their labels in Vietnamese.

| Ubuntu | amd64 | arm64 | Origin |
| --- | --- | --- | --- |
| 22.04 (jammy) | included | included | official Ngó Sen package |
| 24.04 (noble) | included | included | official Ngó Sen package |
| 26.04 (resolute) | Vietfox-patched build | included | official Ngó Sen package for arm64 |

Only the Ubuntu 26.04 amd64 binary currently includes the patched quick menu. The
other five binaries still use the upstream menu until they are rebuilt against
their matching Ubuntu/Fcitx ABI.

The official `.deb` assets were checked against their SHA-256 digests from the
Ngó Sen 1.5.2-1 release before extracting the two engine libraries. The shared
configuration and Vietnamese translation catalog are stored under `engine/share`.
