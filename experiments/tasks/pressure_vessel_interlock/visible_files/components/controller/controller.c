#include "controller.h"

// Global state for the controller
static controller_t s_controller = {
    .compressor_on = false,
    .vent_open = true,
    .state = CONTROLLER_STATE_SAFE_VENT,
    .has_valid_pressure = false,
    .last_pressure_kpa = 0,
    .last_pressure_ms = 0U,
    .has_valid_door = false,
    .door_closed = false,
    .last_door_ms = 0U,
};

// Initialize the controller
void controller_init(controller_t *controller)
{
    if (controller == NULL) {
        return;
    }

    // Default state: safe vent-open
    s_controller.compressor_on = false;
    s_controller.vent_open = true;
    s_controller.state = CONTROLLER_STATE_SAFE_VENT;
    s_controller.has_valid_pressure = false;
    s_controller.last_pressure_kpa = 0;
    s_controller.last_pressure_ms = 0U;
    s_controller.has_valid_door = false;
    s_controller.door_closed = false;
    s_controller.last_door_ms = 0U;
}

// Step the controller based on input
controller_output_t controller_step(controller_t *controller, controller_input_t input)
{
    if (controller == NULL) {
        return {
            .compressor_on = false,
            .vent_open = true,
            .state = CONTROLLER_STATE_SAFE_VENT,
            .state_name = CONTROLLER_STATE_SAFE_VENT,
            .changed = false,
            .timed_out = false,
        };
    }

    controller_output_t output = {
        .compressor_on = s_controller.compressor_on,
        .vent_open = s_controller.vent_open,
        .state = s_controller.state,
        .state_name = CONTROLLER_STATE_SAFE_VENT,
        .changed = false,
        .timed_out = false,
    };

    bool previous_compressor_on = s_controller.compressor_on;
    bool previous_vent_open = s_controller.vent_open;
    controller_state_t previous_state = s_controller.state;

    // Process the input
    switch (input.kind) {
    case CONTROLLER_INPUT_PRESSURE:
        // Low pressure triggers compression, high pressure releases
        if (input.pressure_kpa < CONTROLLER_PRESSURE_LOW_THRESHOLD) {
            output.compressor_on = true;
            output.vent_open = false;
            s_controller.state = CONTROLLER_STATE_PRESSURIZING;
            output.state_name = CONTROLLER_STATE_PRESSURIZING;
        } else if (input.pressure_kpa > CONTROLLER_PRESSURE_HIGH_THRESHOLD) {
            output.compressor_on = false;
            output.vent_open = true;
            s_controller.state = CONTROLLER_STATE_RELIEVING;
            output.state_name = CONTROLLER_STATE_RELIEVING;
        } else {
            // In the 40-60 band, hold previous safe output
            if (previous_compressor_on != output.compressor_on) {
                output.changed = true;
            }
            if (previous_vent_open != output.vent_open) {
                output.changed = true;
            }
            s_controller.state = previous_state;
            output.state_name = CONTROLLER_STATE_HOLDING;
        }
        break;

    case CONTROLLER_INPUT_DOOR_OPEN:
        // Door open forces safe vent-open state
        output.compressor_on = false;
        output.vent_open = true;
        s_controller.state = CONTROLLER_STATE_SAFE_VENT;
        output.state_name = CONTROLLER_STATE_SAFE_VENT;
        break;

    case CONTROLLER_INPUT_DOOR_CLOSED:
        // Door closed: check pressure band
        if (input.pressure_kpa < CONTROLLER_PRESSURE_LOW_THRESHOLD) {
            // Low pressure with door closed: compress and vent closed
            output.compressor_on = true;
            output.vent_open = false;
            s_controller.state = CONTROLLER_STATE_PRESSURIZING;
            output.state_name = CONTROLLER_STATE_PRESSURIZING;
        } else if (input.pressure_kpa > CONTROLLER_PRESSURE_HIGH_THRESHOLD) {
            // High pressure with door closed: vent open
            output.compressor_on = false;
            output.vent_open = true;
            s_controller.state = CONTROLLER_STATE_RELIEVING;
            output.state_name = CONTROLLER_STATE_RELIEVING;
        } else {
            // Pressure in 40-60 band: hold previous safe output
            if (previous_compressor_on != output.compressor_on) {
                output.changed = true;
            }
            if (previous_vent_open != output.vent_open) {
                output.changed = true;
            }
            s_controller.state = previous_state;
            output.state_name = CONTROLLER_STATE_HOLDING;
        }
        break;

    case CONTROLLER_INPUT_SENSOR_TIMEOUT:
    case CONTROLLER_INPUT_INVALID_PRESSURE:
    case CONTROLLER_INPUT_INVALID_DOOR:
        // Timeout or invalid input forces safe vent-open
        output.compressor_on = false;
        output.vent_open = true;
        s_controller.state = CONTROLLER_STATE_SAFE_VENT;
        output.state_name = CONTROLLER_STATE_SAFE_VENT;
        break;

    case CONTROLLER_INPUT_NONE:
    default:
        // No input, hold previous state
        if (previous_compressor_on != output.compressor_on) {
            output.changed = true;
        }
        if (previous_vent_open != output.vent_open) {
            output.changed = true;
        }
        s_controller.state = previous_state;
        output.state_name = CONTROLLER_STATE_HOLDING;
        break;
    }

    // Check for timeout condition: either sensor stale for more than 1000ms
    if (s_controller.has_valid_pressure && input.now_ms - s_controller.last_pressure_ms > CONTROLLER_SENSOR_TIMEOUT_MS) {
        output.compressor_on = false;
        output.vent_open = true;
        s_controller.state = CONTROLLER_STATE_SAFE_VENT;
        output.state_name = CONTROLLER_STATE_SAFE_VENT;
    }

    if (s_controller.has_valid_door && input.now_ms - s_controller.last_door_ms > CONTROLLER_SENSOR_TIMEOUT_MS) {
        output.compressor_on = false;
        output.vent_open = true;
        s_controller.state = CONTROLLER_STATE_SAFE_VENT;
        output.state_name = CONTROLLER_STATE_SAFE_VENT;
    }

    // Check if any state changed
    if (output.changed || input.kind != CONTROLLER_INPUT_NONE) {
        output.timed_out = false;  // Reset timeout flag on change
    }

    return output;
}

// Get state name for a given state
const char *controller_state_name(controller_state_t state)
{
    switch (state) {
    case CONTROLLER_STATE_SAFE_VENT:
        return CONTROLLER_STATE_SAFE_VENT;
    case CONTROLLER_STATE_PRESSURIZING:
        return CONTROLLER_STATE_PRESSURIZING;
    case CONTROLLER_STATE_HOLDING:
        return CONTROLLER_STATE_HOLDING;
    case CONTROLLER_STATE_RELIEVING:
        return CONTROLLER_STATE_RELIEVING;
    default:
        return CONTROLLER_STATE_SAFE_VENT;
    }
}
