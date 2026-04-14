#include "controller.h"

static void controller_set_safe_off(controller_t *controller)
{
    controller->pump_on = false;
    controller->state = CONTROLLER_STATE_SAFE_OFF;
}

void controller_init(controller_t *controller)
{
    if (controller == 0) {
        return;
    }

    controller_set_safe_off(controller);
    controller->has_valid_sensor = false;
    controller->last_level = 0;
    controller->last_valid_sensor_ms = 0U;
}

controller_output_t controller_step(controller_t *controller, controller_input_t input)
{
    controller_output_t output = {
        .pump_on = false,
        .state = CONTROLLER_STATE_SAFE_OFF,
        .state_name = controller_state_name(CONTROLLER_STATE_SAFE_OFF),
        .changed = false,
        .timed_out = false,
    };

    if (controller == 0) {
        return output;
    }

    bool previous_pump_on = controller->pump_on;
    controller_state_t previous_state = controller->state;

    /* Implement the task-specific control policy here (bang-bang with safe hold). */
    bool timed_out_now = false;
    bool timeout_expired = controller->has_valid_sensor &&
        (input.now_ms >= controller->last_valid_sensor_ms) &&
        ((input.now_ms - controller->last_valid_sensor_ms) > CONTROLLER_SENSOR_TIMEOUT_MS);

    switch (input.kind) {
    case CONTROLLER_INPUT_LEVEL:
        if (timeout_expired) {
            timed_out_now = true;
            controller->has_valid_sensor = false;
            controller_set_safe_off(controller);
            break;
        }

        controller->has_valid_sensor = true;
        controller->last_level = input.level;
        controller->last_valid_sensor_ms = input.now_ms;

        if (input.level < CONTROLLER_LEVEL_LOW_THRESHOLD) {
            /* Low level: turn pump ON */
            controller->pump_on = true;
            controller->state = CONTROLLER_STATE_PUMPING;
        } else if (input.level > CONTROLLER_LEVEL_HIGH_THRESHOLD) {
            /* High level: turn pump OFF */
            controller->pump_on = false;
            controller->state = CONTROLLER_STATE_SAFE_OFF;
        } else {
            /* Mid-band: hold previous safe output */
            controller->state = CONTROLLER_STATE_HOLDING;
        }
        break;

    case CONTROLLER_INPUT_SENSOR_TIMEOUT:
    case CONTROLLER_INPUT_INVALID_LEVEL:
        controller->has_valid_sensor = false;
        controller_set_safe_off(controller);
        break;

    case CONTROLLER_INPUT_NONE:
        if (timeout_expired) {
            timed_out_now = true;
            controller->has_valid_sensor = false;
            controller_set_safe_off(controller);
        }
        break;

    default:
        break;
    }

    output.pump_on = controller->pump_on;
    output.state = controller->state;
    output.timed_out = (input.kind == CONTROLLER_INPUT_SENSOR_TIMEOUT) || timed_out_now;
    output.state_name = controller_state_name(controller->state);
    output.changed = (previous_pump_on != controller->pump_on) || (previous_state != controller->state);

    return output;
}

const char *controller_state_name(controller_state_t state)
{
    switch (state) {
    case CONTROLLER_STATE_PUMPING:
        return "STATE PUMPING";
    case CONTROLLER_STATE_HOLDING:
        return "STATE HOLDING";
    case CONTROLLER_STATE_SAFE_OFF:
    default:
        return "STATE SAFE_OFF";
    }
}
