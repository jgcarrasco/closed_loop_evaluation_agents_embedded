#include <stdbool.h>

#include "controller.h"
#include "test_common.h"

static bool startup_defaults_to_safe_vent(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_NONE,
        .pressure_kpa = 0,
        .door_closed = true,
        .now_ms = 0U,
    });

    TEST_ASSERT_FALSE(output.compressor_on);
    TEST_ASSERT_TRUE(output.vent_open);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_SAFE_VENT, output.state);
    return true;
}

static bool stays_safe_until_both_sensors_are_valid(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_PRESSURE,
        .pressure_kpa = 20,
        .door_closed = true,
        .now_ms = 100U,
    });

    TEST_ASSERT_FALSE(output.compressor_on);
    TEST_ASSERT_TRUE(output.vent_open);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_SAFE_VENT, output.state);
    return true;
}

static bool low_pressure_with_closed_door_turns_compressor_on(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_DOOR_CLOSED,
        .pressure_kpa = 0,
        .door_closed = true,
        .now_ms = 100U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_PRESSURE,
        .pressure_kpa = 20,
        .door_closed = true,
        .now_ms = 200U,
    });

    TEST_ASSERT_TRUE(output.compressor_on);
    TEST_ASSERT_FALSE(output.vent_open);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_PRESSURIZING, output.state);
    return true;
}

static bool high_pressure_with_closed_door_opens_vent(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_DOOR_CLOSED,
        .pressure_kpa = 0,
        .door_closed = true,
        .now_ms = 100U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_PRESSURE,
        .pressure_kpa = 70,
        .door_closed = true,
        .now_ms = 200U,
    });

    TEST_ASSERT_FALSE(output.compressor_on);
    TEST_ASSERT_TRUE(output.vent_open);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_RELIEVING, output.state);
    return true;
}

static bool mid_band_holds_previous_safe_pressurizing_state(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_DOOR_CLOSED,
        .pressure_kpa = 0,
        .door_closed = true,
        .now_ms = 100U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_PRESSURE,
        .pressure_kpa = 20,
        .door_closed = true,
        .now_ms = 200U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_PRESSURE,
        .pressure_kpa = 50,
        .door_closed = true,
        .now_ms = 300U,
    });

    TEST_ASSERT_TRUE(output.compressor_on);
    TEST_ASSERT_FALSE(output.vent_open);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_HOLDING, output.state);
    return true;
}

static bool door_open_forces_safe_vent(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_DOOR_CLOSED,
        .pressure_kpa = 0,
        .door_closed = true,
        .now_ms = 100U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_PRESSURE,
        .pressure_kpa = 20,
        .door_closed = true,
        .now_ms = 200U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_DOOR_OPEN,
        .pressure_kpa = 20,
        .door_closed = false,
        .now_ms = 300U,
    });

    TEST_ASSERT_FALSE(output.compressor_on);
    TEST_ASSERT_TRUE(output.vent_open);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_SAFE_VENT, output.state);
    return true;
}

static bool timeout_on_either_sensor_forces_safe_vent(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_DOOR_CLOSED,
        .pressure_kpa = 0,
        .door_closed = true,
        .now_ms = 100U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_PRESSURE,
        .pressure_kpa = 20,
        .door_closed = true,
        .now_ms = 200U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_NONE,
        .pressure_kpa = 0,
        .door_closed = true,
        .now_ms = 1301U,
    });

    TEST_ASSERT_FALSE(output.compressor_on);
    TEST_ASSERT_TRUE(output.vent_open);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_SAFE_VENT, output.state);
    return true;
}

static bool invalid_input_forces_safe_vent(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_DOOR_CLOSED,
        .pressure_kpa = 0,
        .door_closed = true,
        .now_ms = 100U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_PRESSURE,
        .pressure_kpa = 20,
        .door_closed = true,
        .now_ms = 200U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_INVALID_DOOR,
        .pressure_kpa = 0,
        .door_closed = true,
        .now_ms = 300U,
    });

    TEST_ASSERT_FALSE(output.compressor_on);
    TEST_ASSERT_TRUE(output.vent_open);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_SAFE_VENT, output.state);
    return true;
}

int run_controller_tests(void)
{
    const test_case_t cases[] = {
        {"startup defaults to safe vent", startup_defaults_to_safe_vent},
        {"safe until both sensors are valid", stays_safe_until_both_sensors_are_valid},
        {"low pressure with closed door turns compressor on", low_pressure_with_closed_door_turns_compressor_on},
        {"high pressure with closed door opens vent", high_pressure_with_closed_door_opens_vent},
        {"mid-band holds prior pressurizing state", mid_band_holds_previous_safe_pressurizing_state},
        {"door open forces safe vent", door_open_forces_safe_vent},
        {"timeout on either sensor forces safe vent", timeout_on_either_sensor_forces_safe_vent},
        {"invalid input forces safe vent", invalid_input_forces_safe_vent},
    };

    return run_test_cases("controller", cases, sizeof(cases) / sizeof(cases[0]));
}
