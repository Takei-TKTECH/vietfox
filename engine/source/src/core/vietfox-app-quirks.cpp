/*
 * SPDX-FileCopyrightText: 2026 Ngó Sen contributors
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
#include "vietfox-app-quirks.h"

#include "vietfox-strings.h"
#include "vietfox-xtest.h"

namespace ngosen {

    bool forwardsBackspaces(const Field& field) {
        // On wayland_v2 (input-method-v2: Sway, Hyprland) fcitx5 sends forwarded keys through a virtual keyboard.
        if (field.frontend == "wayland" || field.frontend == "wayland_v2") {
            return true;
        }
        if (field.frontend == "xim") {
            // A forwarded key that reaches a client inside one of its own XIM requests comes back to us
            // and lands after the commit (WordCraft); XTEST keys queue in order like typed ones.
            return !xtestAvailable() && !takesSentKeyEvents(field);
        }
        if (field.frontend == "ibus") {
            // SDL takes only commits and preedit from the IM.
            return !isStartsWith(field.program, "SDL");
        }
        if (field.frontend == "dbus") {
            // fcitx5-gtk and fcitx5-qt set one of these; SDL sets neither and handles only commits and preedit.
            return field.keyEventOrderFix || field.surroundingText;
        }
        if (field.frontend == "fcitx4") {
            // Snap apps bundle the fcitx4 GTK module, which sets one of these; SDL 2.0.12 and older speak
            // this protocol too and set at most Preedit.
            return field.formattedPreedit || field.surroundingText;
        }
        return false;
    }

    bool takesSentKeyEvents(const Field& field) {
        if (field.frontend != "xim" || !xsendAvailable())
            return false;
        // Wine applies forwarded keys after a later commit and reports nothing that sets it apart;
        // xterm and XInput2 clients drop sent events, so the rest keep forwarding.
        return isStartsWith(stripDesktopSuffix(field.program), "wine");
    }

    bool ignoresForwardedKeys(const Field& field) {
        if (field.frontend == "ibus") {
            // IBus for GTK4 feeds forwarded keys back into the IM instead of the widget.
            return isStartsWith(field.program, "gtk4-im:");
        }
        // fcitx5-gtk4 discards forwarded keys, and is the D-Bus client that leaves this flag unset.
        return field.frontend == "dbus" && !field.keyEventOrderFix && field.surroundingText;
    }

    bool erasesWithCommittedDel(const Field& field) {
        if (field.surroundingText)
            return false;
        std::string program;
        if (field.frontend == "dbus" && !field.keyEventOrderFix)
            program = field.program;
        else if (field.frontend == "ibus" && isStartsWith(field.program, "gtk4-im:"))
            program = field.program.substr(std::string("gtk4-im:").size());
        else
            return false;
        // Neither GTK4 IM module passes on the terminal input purpose VTE sets; these are the GTK4 VTE terminals.
        program = stripDesktopSuffix(program);
        return program == "ptyxis" || program == "kgx";
    }

    bool selectsOverAutocompletion(const Field& field) {
        if ((field.frontend != "dbus" && field.frontend != "fcitx4") || !forwardsBackspaces(field) || field.surroundingText)
            return false;
        // Terminals match the checks above too, and print Shift+Left instead of selecting.
        const std::string program = stripDesktopSuffix(field.program);
        for (const char* browser : {"chromium", "chrome", "google-chrome", "microsoft-edge", "msedge", "brave", "vivaldi", "opera"}) {
            if (isStartsWith(program, browser))
                return true;
        }
        return false;
    }

    bool surroundingTextLags(const Field& field) {
        return field.frontend == "ibus";
    }

    bool dropsCommitsWithoutFocus(const Field& field) {
        return field.frontend == "wayland" || field.frontend == "wayland_v2";
    }

    bool appliesBackspacesLate(const Field& field) {
        return stripDesktopSuffix(field.program) == "soffice";
    }

    bool reportsFieldOnlyOnKey(const Field& field) {
        // Nothing Calc reports sets it apart from a text field that keeps its text.
        return field.frontend == "wayland" && stripDesktopSuffix(field.program) == "libreoffice-calc";
    }

    bool hidesAddressBarFlag(const Field& field) {
        // Debian names its Firefox ESR program firefox-esr; the forks share Firefox's address bar.
        const std::string program = stripDesktopSuffix(field.program);
        if (isStartsWith(program, "firefox"))
            return true;
        for (const char* fork : {"zen", "librewolf", "waterfox", "floorp", "mullvadbrowser", "icecat"}) {
            if (program == fork)
                return true;
        }
        return false;
    }

} // namespace ngosen
