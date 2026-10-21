/*
 * SPDX-FileCopyrightText: 2026 Ngó Sen contributors
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
#pragma once

#include <string>

namespace ngosen {

    // A Flatpak app reports its app ID (org.mozilla.firefox) where the distro package reports its
    // program name (firefox), which is what the app checks match. Returns the StartupWMClass (else the
    // ID's last part) when a Flatpak export has a desktop file of that name, otherwise the name as is.
    const std::string& normalizeProgramName(const std::string& program);

} // namespace ngosen
