/*
 * SPDX-FileCopyrightText: 2025 Võ Ngô Hoàng Thành <thanhpy2009@gmail.com>
 * SPDX-FileCopyrightText: 2026 Nguyễn Hoàng Kỳ  <nhktmdzhg@gmail.com>
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 */

/**
 * @file vietfox-utils.h
 * @brief Utility functions and global state for Ngó Sen.
 */

#ifndef _FCITX5_NGOSEN_UTILS_H_
#define _FCITX5_NGOSEN_UTILS_H_

#include <fcitx-utils/log.h>
#include <fcitx/inputcontext.h>

#include <string>
#include <vector>

#include "vietfox-config.h"
#include "vietfox-globals.h"
#include "vietfox-log.h"
#include "vietfox-strings.h"

FCITX_DECLARE_LOG_CATEGORY(ngosenLog);

// Forward declaration for fcitx types
using KeySym = uint32_t;

/**
 * @brief Drop surrounding text the client cannot have sent.
 *
 * GNOME Shell multiplexes every window through one IBus input context, and
 * fcitx5 keeps the last SetSurroundingText when focus moves to a client that
 * does not advertise surrounding support (e.g. kitty). Without this, the
 * engine reads the previous window's text as if it belonged to the current one.
 * @param ic Input context.
 * @return True if stale text was dropped.
 */
bool dropStaleSurroundingText(fcitx::InputContext* ic);

/**
 * @brief get environement variable.
 * @param name Name of the variable.
 * @return Value of the variable.
 */
std::string getEnv(const std::string& name);

/** @brief The value of an environment variable, or @p fallback when it is unset or empty. */
std::string envOr(const std::string& name, const std::string& fallback);

/** @brief @p s without leading and trailing spaces, tabs and line breaks. */
std::string trim(const std::string& s);

/** @brief @p dir and @p name joined with one slash. */
std::string joinPath(const std::string& dir, const std::string& name);

/** @brief The non-empty items of @p list separated by @p sep. */
std::vector<std::string> splitList(const std::string& list, char sep);

/** @brief Whether the current user can read the file at @p path. */
bool fileReadable(const std::string& path);

#endif // _FCITX5_NGOSEN_UTILS_H_
