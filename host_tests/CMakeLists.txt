cmake_minimum_required(VERSION 3.20)
project(host_tests C)

set(TASK_ID "tank_fill_drain" CACHE STRING "Task id under host_tests/tasks/")
set(TASK_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/tasks/${TASK_ID}")

if(NOT EXISTS "${TASK_ROOT}/test_controller.c")
    message(FATAL_ERROR "Unknown host-test task id: ${TASK_ID}")
endif()

add_executable(host_tests
    test_main.c
    "${TASK_ROOT}/test_controller.c"
    "${TASK_ROOT}/test_protocol.c"
    ../components/controller/controller.c
    ../components/protocol/protocol.c
)

target_compile_features(host_tests PRIVATE c_std_99)
target_include_directories(host_tests PRIVATE
    .
    "${TASK_ROOT}"
    ../components/controller/include
    ../components/protocol/include
)

enable_testing()
add_test(NAME host_tests COMMAND host_tests)
