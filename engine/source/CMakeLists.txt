cmake_minimum_required(VERSION 3.10)

project(fcitx5-vietfox VERSION 1.5.5)
# The typing log names the version it came from.
add_definitions(-DNGOSEN_VERSION=\"${PROJECT_VERSION}\")
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
option(BUILD_TESTING "Build the tests" OFF)
option(NGOSEN_RUST_CORE "Build the typing core from bamboo-rs/ (Rust) instead of the Go sources in bamboo/" OFF)
option(NGOSEN_CORE_ONLY "Build only the typing logic and its tests, without fcitx5" OFF)

if (NGOSEN_CORE_ONLY)
    set(CMAKE_CXX_STANDARD 17)
    set(CMAKE_CXX_STANDARD_REQUIRED ON)
    set(CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake" ${CMAKE_MODULE_PATH})
    find_package(Pthread REQUIRED)
    if (NGOSEN_RUST_CORE)
        add_subdirectory(bamboo-rs)
    else()
        add_subdirectory(bamboo)
    endif()
    add_subdirectory(src/core)
    enable_testing()
    add_subdirectory(test/core)
    return()
endif()

# The fcitx5 shell around the typing logic (src/core, built as vietfox_core). The addon entry point
# is excluded so the headless tests can link the same sources the module does.
set(ngosen_fcitx_sources
    ${CMAKE_CURRENT_SOURCE_DIR}/src/vietfox-engine.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/vietfox-candidates.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/vietfox-utils.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/vietfox-fcitx-host.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/vietfox-fcitx-log.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/vietfox-program-name.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/vietfox-pointer.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/vietfox-monitor.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/vietfox-icon-resolver.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/emoji.cpp
)

set(REQUIRED_FCITX_VERSION 5.0.14)
find_package(ECM 1.0.0 REQUIRED)
set(CMAKE_MODULE_PATH ${ECM_MODULE_PATH} "${CMAKE_CURRENT_SOURCE_DIR}/cmake" ${CMAKE_MODULE_PATH})
include(FeatureSummary)
include(GNUInstallDirs)
include(ECMUninstallTarget)

find_package(Fcitx5Core ${REQUIRED_FCITX_VERSION} REQUIRED)
find_package(Fcitx5ModuleEmoji REQUIRED)
find_package(Pthread REQUIRED)
find_package(Gettext REQUIRED)

include("${FCITX_INSTALL_CMAKECONFIG_DIR}/Fcitx5Utils/Fcitx5CompilerSettings.cmake")
add_definitions(-DFCITX_GETTEXT_DOMAIN=\"fcitx5-vietfox\")

if (Fcitx5Utils_VERSION VERSION_GREATER_EQUAL "5.1.13")
    add_definitions(-DNGOSEN_USE_MODERN_FCITX_API)
    message(STATUS "Fcitx5 version ${Fcitx5Utils_VERSION} detected: Using modern API")
else()
    message(STATUS "Fcitx5 version ${Fcitx5Utils_VERSION} detected: Using legacy API")
endif()
fcitx5_add_i18n_definition()

add_subdirectory(po)
if (NGOSEN_RUST_CORE)
    add_subdirectory(bamboo-rs)
else()
    add_subdirectory(bamboo)
endif()
add_subdirectory(src)
add_subdirectory(data)
## The Vietfox settings application is implemented in the top-level Python package.

if (BUILD_TESTING)
    include(CTest)
    add_subdirectory(test)
endif()

## Vietfox's own application metadata and GNOME compatibility extension are installed by install.sh.

install(FILES
        LICENSES/GPL-3.0-or-later.txt
        LICENSES/LGPL-2.1-or-later.txt
        LICENSES/OFL-1.1.txt
        DESTINATION ${CMAKE_INSTALL_DATADIR}/licenses/${PROJECT_NAME}
)

feature_summary(WHAT ALL FATAL_ON_MISSING_REQUIRED_PACKAGES)
