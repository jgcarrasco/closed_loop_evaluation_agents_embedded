#include <stdbool.h>

#include "controller.h"
#include "test_common.h"

static bool startup_defaults_to_heater_off(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_NONE,
        .temperature_c = 0,
        .now_ms = 0U,
    });

    TEST_ASSERT_FALSE(output.heater_on);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_SAFE_OFF, output.state);
    return true;
}

static bool low_temperature_turns_heater_on(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 35,
        .now_ms = 100U,
    });

    TEST_ASSERT_TRUE(output.heater_on);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_HEATING, output.state);
    return true;
}

static bool high_temperature_turns_heater_off(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 35,
        .now_ms = 100U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 54,
        .now_ms = 200U,
    });

    TEST_ASSERT_FALSE(output.heater_on);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_SAFE_OFF, output.state);
    return true;
}

static bool lower_mid_band_preserves_heating_state(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 35,
        .now_ms = 100U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 48,
        .now_ms = 200U,
    });

    TEST_ASSERT_TRUE(output.heater_on);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_HOLDING, output.state);
    return true;
}

static bool rising_upper_mid_band_turns_heater_off_early(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 35,
        .now_ms = 100U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 48,
        .now_ms = 200U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 50,
        .now_ms = 300U,
    });

    TEST_ASSERT_FALSE(output.heater_on);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_HOLDING, output.state);
    return true;
}

static bool timeout_forces_safe_off(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 35,
        .now_ms = 100U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_NONE,
        .temperature_c = 0,
        .now_ms = 1201U,
    });

    TEST_ASSERT_FALSE(output.heater_on);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_SAFE_OFF, output.state);
    return true;
}

static bool invalid_input_forces_safe_off(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TEMPERATURE,
        .temperature_c = 35,
        .now_ms = 100U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_INVALID_TEMPERATURE,
        .temperature_c = 0,
        .now_ms = 200U,
    });

    TEST_ASSERT_FALSE(output.heater_on);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_SAFE_OFF, output.state);
    return true;
}

int run_controller_tests(void)
{
    const test_case_t cases[] = {
        {"startup defaults to HEATER OFF", startup_defaults_to_heater_off},
        {"temperature 35 turns heater on", low_temperature_turns_heater_on},
        {"temperature 54 turns heater off", high_temperature_turns_heater_off},
        {"mid-band preserves HEATING state below anticipation zone", lower_mid_band_preserves_heating_state},
        {"rising 50 C turns heater off early", rising_upper_mid_band_turns_heater_off_early},
        {"timeout after 1000 ms forces off", timeout_forces_safe_off},
        {"invalid input forces off", invalid_input_forces_safe_off},
    };

    return run_test_cases("controller", cases, sizeof(cases) / sizeof(cases[0]));
}
