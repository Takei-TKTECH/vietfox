# The typing logic, shared by every input method framework shell. It must not use fcitx5: the
# library gets no fcitx5 include path, so an fcitx5 include here fails the build.
add_library(vietfox_core STATIC
    vietfox-state.cpp
    vietfox-state-emoji.cpp
    vietfox-state-focus.cpp
    vietfox-state-macro.cpp
    vietfox-state-replace.cpp
    vietfox-state-retype.cpp
    vietfox-state-wait.cpp
    vietfox-app-quirks.cpp
    vietfox-globals.cpp
    vietfox-recorder.cpp
    vietfox-strings.cpp
    vietfox-utf8.cpp
    vietfox-xtest.cpp
)
set_target_properties(vietfox_core PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(vietfox_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
# The shell provides ngosen::writeLog and ngosen::logEnabled (vietfox-log.h).
target_link_libraries(vietfox_core PUBLIC
    Bamboo::Core
    Pthread::Pthread
    ${CMAKE_DL_LIBS}
)
