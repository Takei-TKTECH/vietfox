/*
 * SPDX-FileCopyrightText: 2026 Ngó Sen contributors
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
#include "vietfox-migration.h"

#include <fcitx-config/iniparser.h>
#include <fcitx-utils/log.h>
#include <fcitx/addonfactory.h>
#include <fcitx/addoninstance.h>
#include <fcitx/addonmanager.h>
#include <fcitx/instance.h>
#if NGOSEN_USE_MODERN_FCITX_API
#include <fcitx-utils/standardpaths.h>
#else
#include <fcitx-utils/standardpath.h>
#endif

#include <chrono>
#include <thread>

#include <unistd.h>

namespace {

    // Loaded at startup, before fcitx5 reads its profile, so profiles using an older input method
    // ID keep working after upgrading to Vietfox.
    class VietfoxMigration : public fcitx::AddonInstance {
      public:
        explicit VietfoxMigration(fcitx::Instance* instance) {
            copyUserFiles();
            renameInProfile(instance->willTryReplace());
        }

      private:
        static void copyUserFiles() {
#if NGOSEN_USE_MODERN_FCITX_API
            const auto& paths   = fcitx::StandardPaths::global();
            const auto  confDir = paths.userDirectory(fcitx::StandardPathsType::PkgConfig) / "conf";
            const auto  dataDir = paths.userDirectory(fcitx::StandardPathsType::PkgData);
#else
            const auto&                 paths = fcitx::StandardPath::global();
            const std::filesystem::path confDir(paths.userDirectory(fcitx::StandardPath::Type::PkgConfig) + "/conf");
            const std::filesystem::path dataDir(paths.userDirectory(fcitx::StandardPath::Type::PkgData));
#endif
            for (const auto& name : ngosen::copyLegacyFiles(confDir, ngosen::legacyConfigFiles())) {
                FCITX_INFO() << "Ngó Sen: copied settings to " << name;
            }
            ngosen::copyLegacyFiles(dataDir, {{"lotus/vietnamese.cm.dict", "ngosen/vietnamese.cm.dict"}});
        }

        // `fcitx5 -r` takes over from the running fcitx5, which then saves its profile, still under
        // the old name, as it exits. That happens after this addon runs (it loads after dbus, which
        // asks the old one to quit), so wait for it or it overwrites the rename.
        static bool waitForPreviousInstance() {
            using namespace std::chrono_literals;
            const auto self   = static_cast<int>(getpid());
            bool       waited = false;
            for (auto deadline = std::chrono::steady_clock::now() + 3s; std::chrono::steady_clock::now() < deadline;) {
                if (ngosen::processesNamed("/proc", "fcitx5", getuid(), self).empty()) {
                    return waited;
                }
                waited = true;
                std::this_thread::sleep_for(50ms);
            }
            FCITX_WARN() << "Ngó Sen: the previous fcitx5 is still running";
            return waited;
        }

        static void renameInProfile(bool replacing) {
            // With fcitx5-lotus installed, "lotus" in the profile is that input method; leave it.
#if NGOSEN_USE_MODERN_FCITX_API
            if (!fcitx::StandardPaths::global().locate(fcitx::StandardPathsType::PkgData, "inputmethod/lotus.conf").empty()) {
                return;
            }
            const auto type = fcitx::StandardPathsType::PkgConfig;
#else
            if (!fcitx::StandardPath::global().locate(fcitx::StandardPath::Type::PkgData, "inputmethod/lotus.conf").empty()) {
                return;
            }
            const auto type = fcitx::StandardPath::Type::PkgConfig;
#endif
            const auto readRenamed = [type](fcitx::RawConfig& profile, const std::string& from) {
                fcitx::readAsIni(profile, type, "profile");
                return ngosen::renameProfileInputMethod(profile, from, ngosen::InputMethod);
            };
            fcitx::RawConfig profile;
            std::string oldInputMethod = ngosen::LegacyInputMethod;
            if (!readRenamed(profile, oldInputMethod)) {
                oldInputMethod = "lotus";
                if (!readRenamed(profile, oldInputMethod)) {
                    return;
                }
            }
            if (replacing && waitForPreviousInstance()) {
                // Start again from the profile it saved on the way out.
                fcitx::RawConfig saved;
                if (!readRenamed(saved, oldInputMethod)) {
                    return;
                }
                fcitx::safeSaveAsIni(saved, type, "profile");
            } else {
                fcitx::safeSaveAsIni(profile, type, "profile");
            }
            FCITX_INFO() << "Vietfox: migrated input method " << oldInputMethod << " to Vietfox";
        }
    };

    class VietfoxMigrationFactory : public fcitx::AddonFactory {
      public:
        fcitx::AddonInstance* create(fcitx::AddonManager* manager) override {
            return new VietfoxMigration(manager->instance());
        }
    };

} // namespace

FCITX_ADDON_FACTORY(VietfoxMigrationFactory)
