#include <stdbool.h>

#include "controller.h"
#include "test_common.h"

/* Prose-only task: grade documented pump behavior, not internal state labels. */

static bool startup_defaults_to_pump_off(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_NONE,
        .level = 0,
        .now_ms = 0U,
    });

    TEST_ASSERT_FALSE(output.pump_on);
    return true;
}

static bool low_level_turns_pump_on(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .level = 20,
        .now_ms = 100U,
    });

    TEST_ASSERT_TRUE(output.pump_on);
    return true;
}

static bool high_level_turns_pump_off(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .level = 20,
        .now_ms = 100U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .level = 85,
        .now_ms = 200U,
    });

    TEST_ASSERT_FALSE(output.pump_on);
    return true;
}

static bool mid_band_preserves_current_safe_on_state(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .level = 20,
        .now_ms = 100U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .level = 50,
        .now_ms = 200U,
    });

    TEST_ASSERT_TRUE(output.pump_on);
    return true;
}

static bool mid_band_preserves_current_safe_off_state(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .level = 85,
        .now_ms = 100U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .level = 50,
        .now_ms = 200U,
    });

    TEST_ASSERT_FALSE(output.pump_on);
    return true;
}

static bool timeout_forces_safe_off(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .level = 20,
        .now_ms = 100U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_NONE,
        .level = 0,
        .now_ms = 1201U,
    });

    TEST_ASSERT_FALSE(output.pump_on);
    return true;
}

static bool invalid_input_forces_safe_off(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .level = 20,
        .now_ms = 100U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_INVALID_LEVEL,
        .level = 0,
        .now_ms = 200U,
    });

    TEST_ASSERT_FALSE(output.pump_on);
    return true;
}

int run_controller_tests(void)
{
    const test_case_t cases[] = {
        {"startup defaults to PUMP OFF", startup_defaults_to_pump_off},
        {"level 20 turns pump on", low_level_turns_pump_on},
        {"level 85 turns pump off", high_level_turns_pump_off},
        {"mid-band preserves ON state", mid_band_preserves_current_safe_on_state},
        {"mid-band preserves OFF state", mid_band_preserves_current_safe_off_state},
        {"timeout after 1000 ms forces off", timeout_forces_safe_off},
        {"invalid input forces off", invalid_input_forces_safe_off},
    };

    return run_test_cases("controller", cases, sizeof(cases) / sizeof(cases[0]));
}
