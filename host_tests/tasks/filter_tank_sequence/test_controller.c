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
        .turbidity_ntu = 0,
        .level = 0,
        .now_ms = 0U,
    });

    TEST_ASSERT_FALSE(output.filter_on);
    TEST_ASSERT_FALSE(output.drain_open);
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
        .turbidity_ntu = 0,
        .level = 72,
        .now_ms = 100U,
    });

    TEST_ASSERT_FALSE(output.filter_on);
    TEST_ASSERT_FALSE(output.drain_open);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_SAFE_IDLE, output.state);
    return true;
}

static bool cloudy_tank_starts_filtering(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .turbidity_ntu = 0,
        .level = 72,
        .now_ms = 100U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TURBIDITY,
        .turbidity_ntu = 80,
        .level = 72,
        .now_ms = 200U,
    });

    TEST_ASSERT_TRUE(output.filter_on);
    TEST_ASSERT_FALSE(output.drain_open);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_FILTERING, output.state);
    return true;
}

static bool three_clear_turbidity_samples_enter_settling(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .turbidity_ntu = 0,
        .level = 72,
        .now_ms = 100U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TURBIDITY,
        .turbidity_ntu = 34,
        .level = 72,
        .now_ms = 200U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TURBIDITY,
        .turbidity_ntu = 28,
        .level = 72,
        .now_ms = 300U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TURBIDITY,
        .turbidity_ntu = 20,
        .level = 72,
        .now_ms = 400U,
    });

    TEST_ASSERT_FALSE(output.filter_on);
    TEST_ASSERT_FALSE(output.drain_open);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_SETTLING, output.state);
    return true;
}

static bool disturbance_during_settling_returns_to_filtering(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .turbidity_ntu = 0,
        .level = 72,
        .now_ms = 100U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TURBIDITY,
        .turbidity_ntu = 34,
        .level = 72,
        .now_ms = 200U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TURBIDITY,
        .turbidity_ntu = 28,
        .level = 72,
        .now_ms = 300U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TURBIDITY,
        .turbidity_ntu = 20,
        .level = 72,
        .now_ms = 400U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TURBIDITY,
        .turbidity_ntu = 45,
        .level = 72,
        .now_ms = 500U,
    });

    TEST_ASSERT_TRUE(output.filter_on);
    TEST_ASSERT_FALSE(output.drain_open);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_FILTERING, output.state);
    return true;
}

static bool settled_clear_tank_opens_drain(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .turbidity_ntu = 0,
        .level = 72,
        .now_ms = 100U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TURBIDITY,
        .turbidity_ntu = 34,
        .level = 72,
        .now_ms = 200U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TURBIDITY,
        .turbidity_ntu = 28,
        .level = 72,
        .now_ms = 300U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TURBIDITY,
        .turbidity_ntu = 20,
        .level = 72,
        .now_ms = 400U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_NONE,
        .turbidity_ntu = 20,
        .level = 72,
        .now_ms = 800U,
    });

    TEST_ASSERT_FALSE(output.filter_on);
    TEST_ASSERT_TRUE(output.drain_open);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_DRAINING, output.state);
    return true;
}

static bool low_level_completes_cycle(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .turbidity_ntu = 0,
        .level = 72,
        .now_ms = 100U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TURBIDITY,
        .turbidity_ntu = 34,
        .level = 72,
        .now_ms = 200U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TURBIDITY,
        .turbidity_ntu = 28,
        .level = 72,
        .now_ms = 300U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TURBIDITY,
        .turbidity_ntu = 20,
        .level = 72,
        .now_ms = 400U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_NONE,
        .turbidity_ntu = 20,
        .level = 72,
        .now_ms = 700U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .turbidity_ntu = 20,
        .level = 10,
        .now_ms = 800U,
    });

    TEST_ASSERT_FALSE(output.filter_on);
    TEST_ASSERT_FALSE(output.drain_open);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_COMPLETE, output.state);
    return true;
}

static bool timeout_forces_safe_idle(void)
{
    controller_t controller;
    controller_output_t output;

    controller_init(&controller);
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_LEVEL,
        .turbidity_ntu = 0,
        .level = 72,
        .now_ms = 100U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TURBIDITY,
        .turbidity_ntu = 80,
        .level = 72,
        .now_ms = 200U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_NONE,
        .turbidity_ntu = 80,
        .level = 72,
        .now_ms = 1301U,
    });

    TEST_ASSERT_FALSE(output.filter_on);
    TEST_ASSERT_FALSE(output.drain_open);
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
        .turbidity_ntu = 0,
        .level = 72,
        .now_ms = 100U,
    });
    (void) controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_TURBIDITY,
        .turbidity_ntu = 80,
        .level = 72,
        .now_ms = 200U,
    });
    output = controller_step(&controller, (controller_input_t) {
        .kind = CONTROLLER_INPUT_INVALID_TURBIDITY,
        .turbidity_ntu = 0,
        .level = 72,
        .now_ms = 300U,
    });

    TEST_ASSERT_FALSE(output.filter_on);
    TEST_ASSERT_FALSE(output.drain_open);
    TEST_ASSERT_INT_EQ(CONTROLLER_STATE_SAFE_IDLE, output.state);
    return true;
}

int run_controller_tests(void)
{
    const test_case_t cases[] = {
        {"startup defaults to safe idle", startup_defaults_to_safe_idle},
        {"safe until both sensors are valid", stays_safe_until_both_sensors_are_valid},
        {"cloudy tank starts filtering", cloudy_tank_starts_filtering},
        {"three clear turbidity samples enter settling", three_clear_turbidity_samples_enter_settling},
        {"disturbance during settling returns to filtering", disturbance_during_settling_returns_to_filtering},
        {"settled clear tank opens drain", settled_clear_tank_opens_drain},
        {"low level completes cycle", low_level_completes_cycle},
        {"timeout forces safe idle", timeout_forces_safe_idle},
        {"invalid input forces safe idle", invalid_input_forces_safe_idle},
    };

    return run_test_cases("controller", cases, sizeof(cases) / sizeof(cases[0]));
}
