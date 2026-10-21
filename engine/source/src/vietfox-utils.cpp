/*
 * SPDX-FileCopyrightText: 2025 Võ Ngô Hoàng Thành <thanhpy2009@gmail.com>
 * SPDX-FileCopyrightText: 2026 Nguyễn Hoàng Kỳ  <nhktmdzhg@gmail.com>
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 */
#include "vietfox-utils.h"
#include "vietfox-config.h"

#include <cstddef>
#include <cstdlib>
#include <string_view>
#include <fcitx-utils/utf8.h>
#include <unistd.h>

#include <algorithm>
#include <cerrno>
#include <cstring>
#include <sstream>

FCITX_DEFINE_LOG_CATEGORY(ngosenLog, "ngosen", fcitx::LogLevel::NoLog);

bool dropStaleSurroundingText(fcitx::InputContext* ic) {
    if (ic == nullptr || ic->capabilityFlags().test(fcitx::CapabilityFlag::SurroundingText) || !ic->surroundingText().isValid()) {
        return false;
    }
    ic->surroundingText().invalidate();
    return true;
}

std::string getEnv(const std::string& name) {
    const char* value = std::getenv(name.c_str());
    return ((value != nullptr) && ((*value) != 0)) ? value : "";
}

std::string envOr(const std::string& name, const std::string& fallback) {
    std::string value = getEnv(name);
    return !value.empty() ? value : fallback;
}

std::string trim(const std::string& s) {
    const auto begin = s.find_first_not_of(" \t\r\n");
    if (begin == std::string::npos)
        return "";
    const auto end = s.find_last_not_of(" \t\r\n");
    return s.substr(begin, end - begin + 1);
}

std::string joinPath(const std::string& dir, const std::string& name) {
    if (dir.empty())
        return name;
    if (dir.back() == '/')
        return dir + name;
    return dir + "/" + name;
}

std::vector<std::string> splitList(const std::string& list, char sep) {
    std::vector<std::string> result;
    std::stringstream        ss(list);
    std::string              item;
    while (std::getline(ss, item, sep)) {
        if (!item.empty())
            result.push_back(item);
    }
    return result;
}

bool fileReadable(const std::string& path) {
    return !path.empty() && access(path.c_str(), R_OK) == 0;
}
