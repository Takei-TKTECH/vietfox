add_subdirectory(core)

add_library(vietfox MODULE vietfox.cpp ${ngosen_fcitx_sources})
set_target_properties(vietfox PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_link_options(vietfox PRIVATE "-Wl,-exclude-libs,ALL")
target_link_libraries(vietfox
	vietfox_core
	Fcitx5::Core
	Fcitx5::Config
  Fcitx5::Module::Emoji
	Bamboo::Core
	Pthread::Pthread
)

target_include_directories(vietfox PRIVATE
    ${PROJECT_BINARY_DIR}
)
target_compile_definitions(vietfox PRIVATE
    NGOSEN_SETTINGS_PATH=\"${CMAKE_INSTALL_FULL_BINDIR}/vietfox\"
    NGOSEN_ICON_DIR=\"${CMAKE_INSTALL_FULL_DATADIR}/icons/hicolor/scalable/apps\"
)
install(TARGETS vietfox DESTINATION "${CMAKE_INSTALL_LIBDIR}/fcitx5")

fcitx5_translate_desktop_file(vietfox.conf.in vietfox.conf)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/vietfox.conf" DESTINATION "${CMAKE_INSTALL_DATADIR}/fcitx5/inputmethod")
configure_file(vietfox-addon.conf.in.in vietfox-addon.conf.in)
fcitx5_translate_desktop_file("${CMAKE_CURRENT_BINARY_DIR}/vietfox-addon.conf.in" vietfox-addon.conf)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/vietfox-addon.conf" RENAME vietfox.conf DESTINATION "${FCITX_INSTALL_PKGDATADIR}/addon")

add_library(vietfox_migration STATIC vietfox-migration.cpp)
set_target_properties(vietfox_migration PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_link_libraries(vietfox_migration PUBLIC Fcitx5::Config)
target_include_directories(vietfox_migration PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

# Not on demand, so it runs before fcitx5 reads its profile.
add_library(vietfoxmigrate MODULE vietfox-migrate-addon.cpp)
target_link_options(vietfoxmigrate PRIVATE "-Wl,-exclude-libs,ALL")
target_link_libraries(vietfoxmigrate PRIVATE vietfox_migration Fcitx5::Core)
install(TARGETS vietfoxmigrate DESTINATION "${CMAKE_INSTALL_LIBDIR}/fcitx5")
configure_file(vietfoxmigrate.conf.in vietfoxmigrate.conf @ONLY)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/vietfoxmigrate.conf" DESTINATION "${FCITX_INSTALL_PKGDATADIR}/addon")
