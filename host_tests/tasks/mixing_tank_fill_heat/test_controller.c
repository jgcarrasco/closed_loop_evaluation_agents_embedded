#include <stdbool.h>

#include "controller.h"
#include "test_common.h"

static bool startup_defaults_to_safe_idle(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_NONE,
        .temperature_c = 0,
        .level = 0,
        .now_ms = 0U,
    });

    TEST_ASSERT_FALSE(output.inlet_open);
    TEST_ASSERT_FALSE(output.heater_on);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_SAFE_IDLE, output.state);
    return true;
}

static bool stays_safe_until_both_sensors_are_valid(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .temperature_c = 0,
        .level = 40,
        .now_ms = 100U,
    });

    TEST_ASSERT_FALSE(output.inlet_open);
    TEST_ASSERT_FALSE(output.heater_on);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_SAFE_IDLE, output.state);
    return true;
}

static bool low_level_opens_inlet_and_keeps_heater_off(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 30,
        .level = 0,
        .now_ms = 100U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .temperature_c = 30,
        .level = 40,
        .now_ms = 200U,
    });

    TEST_ASSERT_TRUE(output.inlet_open);
    TEST_ASSERT_FALSE(output.heater_on);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_FILLING, output.state);
    return true;
}

static bool adequate_level_and_low_temp_turns_heater_on(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .temperature_c = 0,
        .level = 65,
        .now_ms = 100U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 30,
        .level = 65,
        .now_ms = 200U,
    });

    TEST_ASSERT_FALSE(output.inlet_open);
    TEST_ASSERT_TRUE(output.heater_on);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_HEATING, output.state);
    return true;
}

static bool low_level_guard_turns_heater_off(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .temperature_c = 0,
        .level = 65,
        .now_ms = 100U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 30,
        .level = 65,
        .now_ms = 200U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .temperature_c = 30,
        .level = 50,
        .now_ms = 300U,
    });

    TEST_ASSERT_TRUE(output.inlet_open);
    TEST_ASSERT_FALSE(output.heater_on);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_FILLING, output.state);
    return true;
}

static bool rising_upper_band_turns_heater_off_early(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .temperature_c = 0,
        .level = 65,
        .now_ms = 100U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 40,
        .level = 65,
        .now_ms = 200U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 46,
        .level = 65,
        .now_ms = 300U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 47,
        .level = 65,
        .now_ms = 400U,
    });

    TEST_ASSERT_FALSE(output.inlet_open);
    TEST_ASSERT_FALSE(output.heater_on);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_HOLDING, output.state);
    return true;
}

static bool timeout_forces_safe_idle(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .temperature_c = 0,
        .level = 65,
        .now_ms = 100U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 30,
        .level = 65,
        .now_ms = 200U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_NONE,
        .temperature_c = 0,
        .level = 0,
        .now_ms = 1301U,
    });

    TEST_ASSERT_FALSE(output.inlet_open);
    TEST_ASSERT_FALSE(output.heater_on);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_SAFE_IDLE, output.state);
    return true;
}

static bool invalid_input_forces_safe_idle(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .temperature_c = 0,
        .level = 65,
        .now_ms = 100U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 30,
        .level = 65,
        .now_ms = 200U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_INVALID_LEVEL,
        .temperature_c = 0,
        .level = 0,
        .now_ms = 300U,
    });

    TEST_ASSERT_FALSE(output.inlet_open);
    TEST_ASSERT_FALSE(output.heater_on);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_SAFE_IDLE, output.state);
    return true;
}

int run_controller_tests(void)
{
    const test_case_t cases[] = {
        {"startup defaults to safe idle", startup_defaults_to_safe_idle},
        {"safe until both sensors are valid", stays_safe_until_both_sensors_are_valid},
        {"low level opens inlet and keeps heater off", low_level_opens_inlet_and_keeps_heater_off},
        {"adequate level and low temp turns heater on", adequate_level_and_low_temp_turns_heater_on},
        {"low level guard turns heater off", low_level_guard_turns_heater_off},
        {"rising upper band turns heater off early", rising_upper_band_turns_heater_off_early},
        {"timeout forces safe idle", timeout_forces_safe_idle},
        {"invalid input forces safe idle", invalid_input_forces_safe_idle},
    };

    return run_test_cases("controller", cases, sizeof(cases) / sizeof(cases[0]));
}
