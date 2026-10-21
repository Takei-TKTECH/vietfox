/*
 * SPDX-FileCopyrightText: 2026 Ngó Sen contributors
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
#include "vietfox-program-name.h"

#include "vietfox-strings.h"

#include <fcitx-config/iniparser.h>
#include <fcitx-config/rawconfig.h>
#if NGOSEN_USE_MODERN_FCITX_API
#include <fcitx-utils/standardpaths.h>
#else
#include <fcitx-utils/standardpath.h>
#endif

#include <algorithm>
#include <cctype>
#include <cstdio>
#include <unordered_map>
#include <vector>

namespace ngosen {

    namespace {
        std::string lowercaseWithoutSpaces(std::string text) {
            text.erase(std::remove(text.begin(), text.end(), ' '), text.end());
            std::transform(text.begin(), text.end(), text.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
            return text;
        }

        bool looksLikeAppId(const std::string& name) {
            return std::count(name.begin(), name.end(), '.') >= 2 && name.find('/') == std::string::npos;
        }

        std::vector<std::string> desktopFiles(const std::string& name) {
            const std::string        file = "applications/" + name + ".desktop";
            std::vector<std::string> found;
#if NGOSEN_USE_MODERN_FCITX_API
            for (const auto& path : fcitx::StandardPaths::global().locateAll(fcitx::StandardPathsType::Data, file))
                found.push_back(path.string());
#else
            found = fcitx::StandardPath::global().locateAll(fcitx::StandardPath::Type::Data, file);
#endif
            return found;
        }

        std::string programForAppId(const std::string& appId, const fcitx::RawConfig& desktopEntry) {
            const std::string* wmClass = desktopEntry.valueByPath("Desktop Entry/StartupWMClass");
            // Mullvad Browser's class is "Mullvad Browser", Lutris gives its app ID.
            if (wmClass && !wmClass->empty() && !looksLikeAppId(*wmClass))
                return lowercaseWithoutSpaces(*wmClass);
            return lowercaseWithoutSpaces(appId.substr(appId.rfind('.') + 1));
        }

        std::string resolve(const std::string& program) {
            const std::string name = stripDesktopSuffix(program);
            if (!looksLikeAppId(name))
                return program;
            for (const auto& path : desktopFiles(name)) {
                // A native app may use a reverse-DNS name too; only a Flatpak export proves the app ID.
                if (path.find("/flatpak/exports/share/applications/") == std::string::npos)
                    continue;
                FILE* file = std::fopen(path.c_str(), "r");
                if (!file)
                    continue;
                fcitx::RawConfig entry;
                fcitx::readFromIni(entry, file);
                std::fclose(file);
                return programForAppId(name, entry);
            }
            return program;
        }
    } // namespace

    const std::string& normalizeProgramName(const std::string& program) {
        static std::unordered_map<std::string, std::string> cache;
        auto                                                it = cache.find(program);
        if (it == cache.end())
            it = cache.emplace(program, resolve(program)).first;
        return it->second;
    }

} // namespace ngosen
