#include "controller.h"

static void controller_set_safe_idle(controller_t *controller)
{
    controller->inlet_open = false;
    controller->heater_on = false;
    controller->state = CONTROLLER_STATE_SAFE_IDLE;
}

void controller_init(controller_t *controller)
{
    if (controller == 0) {
        return;
    }

    controller_set_safe_idle(controller);
    controller->has_valid_temperature = false;
    controller->previous_temperature_c = 0;
    controller->last_temperature_c = 0;
    controller->last_temperature_ms = 0U;
    controller->has_valid_level = false;
    controller->last_level = 0;
    controller->last_level_ms = 0U;
}

controller_output_t controller_step(controller_t *controller, controller_input_t input)
{
    controller_output_t output = {
        .inlet_open = false,
        .heater_on = false,
        .state = CONTROLLER_STATE_SAFE_IDLE,
        .state_name = controller_state_name(CONTROLLER_STATE_SAFE_IDLE),
        .changed = false,
        .timed_out = false,
    };
    bool previous_inlet_open;
    bool previous_heater_on;
    controller_state_t previous_state;

    if (controller == 0) {
        return output;
    }

    previous_inlet_open = controller->inlet_open;
    previous_heater_on = controller->heater_on;
    previous_state = controller->state;

    /* TODO: implement the fill-and-heat policy here. */
    switch (input.kind) {
    case CONTROLLER_INPUT_TEMPERATURE:
        controller->has_valid_temperature = true;
        controller->previous_temperature_c = controller->last_temperature_c;
        controller->last_temperature_c = input.temperature_c;
        controller->last_temperature_ms = input.now_ms;
        controller_set_safe_idle(controller);
        break;
    case CONTROLLER_INPUT_LEVEL:
        controller->has_valid_level = true;
        controller->last_level = input.level;
        controller->last_level_ms = input.now_ms;
        controller_set_safe_idle(controller);
        break;
    case CONTROLLER_INPUT_SENSOR_TIMEOUT:
    case CONTROLLER_INPUT_INVALID_TEMPERATURE:
    case CONTROLLER_INPUT_INVALID_LEVEL:
        controller->has_valid_temperature = false;
        controller->has_valid_level = false;
        controller_set_safe_idle(controller);
        break;
    case CONTROLLER_INPUT_NONE:
    default:
        controller_set_safe_idle(controller);
        break;
    }

    output.inlet_open = controller->inlet_open;
    output.heater_on = controller->heater_on;
    output.state = controller->state;
    output.state_name = controller_state_name(controller->state);
    output.changed =
        (previous_inlet_open != controller->inlet_open) ||
        (previous_heater_on != controller->heater_on) ||
        (previous_state != controller->state);
    return output;
}

const char *controller_state_name(controller_state_t state)
{
    switch (state) {
    case CONTROLLER_STATE_FILLING:
        return "STATE FILLING";
    case CONTROLLER_STATE_HEATING:
        return "STATE HEATING";
    case CONTROLLER_STATE_HOLDING:
        return "STATE HOLDING";
    case CONTROLLER_STATE_SAFE_IDLE:
    default:
        return "STATE SAFE_IDLE";
    }
}
