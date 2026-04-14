#include "controller.h"

static void controller_set_safe_off(controller_t *controller)
{
    controller->heater_on = false;
    controller->state = CONTROLLER_STATE_SAFE_OFF;
}

void controller_init(controller_t *controller)
{
    if (controller == 0) {
        return;
    }

    controller_set_safe_off(controller);
    controller->has_valid_sensor = false;
    controller->last_temperature_c = 0;
    controller->last_valid_sensor_ms = 0U;
}

controller_output_t controller_step(controller_t *controller, controller_input_t input)
{
    controller_output_t output = {
        .heater_on = false,
        .state = CONTROLLER_STATE_SAFE_OFF,
        .state_name = controller_state_name(CONTROLLER_STATE_SAFE_OFF),
        .changed = false,
        .timed_out = false,
    };
    bool previous_heater_on;
    controller_state_t previous_state;

    if (controller == 0) {
        return output;
    }

    previous_heater_on = controller->heater_on;
    previous_state = controller->state;

    /* TODO: Implement the task-specific thermal control policy here. */
    switch (input.kind) {
    case CONTROLLER_INPUT_TEMPERATURE:
        controller->has_valid_sensor = true;
        controller->last_temperature_c = input.temperature_c;
        controller->last_valid_sensor_ms = input.now_ms;
        controller_set_safe_off(controller);
        break;
    case CONTROLLER_INPUT_SENSOR_TIMEOUT:
    case CONTROLLER_INPUT_INVALID_TEMPERATURE:
        controller->has_valid_sensor = false;
        controller_set_safe_off(controller);
        break;
    case CONTROLLER_INPUT_NONE:
    default:
        controller_set_safe_off(controller);
        break;
    }

    output.heater_on = controller->heater_on;
    output.state = controller->state;
    output.state_name = controller_state_name(controller->state);
    output.changed = (previous_heater_on != controller->heater_on) || (previous_state != controller->state);

    return output;
}

const char *controller_state_name(controller_state_t state)
{
    switch (state) {
    case CONTROLLER_STATE_HEATING:
        return "STATE HEATING";
    case CONTROLLER_STATE_HOLDING:
        return "STATE HOLDING";
    case CONTROLLER_STATE_SAFE_OFF:
    default:
        return "STATE SAFE_OFF";
    }
}

