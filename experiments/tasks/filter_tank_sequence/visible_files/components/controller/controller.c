#include "controller.h"

static void controller_set_safe_idle(controller_t *controller)
{
    controller->filter_on = false;
    controller->drain_open = false;
    controller->state = CONTROLLER_STATE_SAFE_IDLE;
}

void controller_init(controller_t *controller)
{
    if (controller == 0) {
        return;
    }

    controller_set_safe_idle(controller);
    controller->has_valid_turbidity = false;
    controller->last_turbidity_ntu = 0;
    controller->last_turbidity_ms = 0U;
    controller->has_valid_level = false;
    controller->last_level = 0;
    controller->last_level_ms = 0U;
    controller->clear_streak_count = 0;
    controller->settling_started_ms = 0U;
}

controller_output_t controller_step(controller_t *controller, controller_input_t input)
{
    controller_output_t output = {
        .filter_on = false,
        .drain_open = false,
        .state = CONTROLLER_STATE_SAFE_IDLE,
        .state_name = controller_state_name(CONTROLLER_STATE_SAFE_IDLE),
        .changed = false,
        .timed_out = false,
    };
    bool previous_filter_on;
    bool previous_drain_open;
    controller_state_t previous_state;

    if (controller == 0) {
        return output;
    }

    previous_filter_on = controller->filter_on;
    previous_drain_open = controller->drain_open;
    previous_state = controller->state;

    /* TODO: implement the filtering, settling, and draining state machine here. */
    switch (input.kind) {
    case CONTROLLER_INPUT_TURBIDITY:
        controller->has_valid_turbidity = true;
        controller->last_turbidity_ntu = input.turbidity_ntu;
        controller->last_turbidity_ms = input.now_ms;
        controller_set_safe_idle(controller);
        break;
    case CONTROLLER_INPUT_LEVEL:
        controller->has_valid_level = true;
        controller->last_level = input.level;
        controller->last_level_ms = input.now_ms;
        controller_set_safe_idle(controller);
        break;
    case CONTROLLER_INPUT_SENSOR_TIMEOUT:
    case CONTROLLER_INPUT_INVALID_TURBIDITY:
    case CONTROLLER_INPUT_INVALID_LEVEL:
        controller->has_valid_turbidity = false;
        controller->has_valid_level = false;
        controller->clear_streak_count = 0;
        controller->settling_started_ms = 0U;
        controller_set_safe_idle(controller);
        break;
    case CONTROLLER_INPUT_NONE:
    default:
        controller_set_safe_idle(controller);
        break;
    }

    output.filter_on = controller->filter_on;
    output.drain_open = controller->drain_open;
    output.state = controller->state;
    output.state_name = controller_state_name(controller->state);
    output.changed =
        (previous_filter_on != controller->filter_on) ||
        (previous_drain_open != controller->drain_open) ||
        (previous_state != controller->state);
    return output;
}

const char *controller_state_name(controller_state_t state)
{
    switch (state) {
    case CONTROLLER_STATE_FILTERING:
        return "STATE FILTERING";
    case CONTROLLER_STATE_SETTLING:
        return "STATE SETTLING";
    case CONTROLLER_STATE_DRAINING:
        return "STATE DRAINING";
    case CONTROLLER_STATE_COMPLETE:
        return "STATE COMPLETE";
    case CONTROLLER_STATE_SAFE_IDLE:
    default:
        return "STATE SAFE_IDLE";
    }
}
