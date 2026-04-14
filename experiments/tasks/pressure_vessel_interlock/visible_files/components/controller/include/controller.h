#ifndef CONTROLLER_H
#define CONTROLLER_H

#include <stdbool.h>
#include <stdint.h>

// Controller state names
#define CONTROLLER_STATE_SAFE_VENT "STATE SAFE_VENT"
#define CONTROLLER_STATE_PRESSURIZING "STATE PRESSURIZING"
#define CONTROLLER_STATE_HOLDING "STATE HOLDING"
#define CONTROLLER_STATE_RELIEVING "STATE RELIEVING"

// Thresholds
#define CONTROLLER_PRESSURE_LOW_THRESHOLD 40
#define CONTROLLER_PRESSURE_HIGH_THRESHOLD 60
#define CONTROLLER_SENSOR_TIMEOUT_MS 1000U

// Input kinds
typedef enum {
    CONTROLLER_INPUT_NONE = 0,
    CONTROLLER_INPUT_PRESSURE,
    CONTROLLER_INPUT_DOOR_OPEN,
    CONTROLLER_INPUT_DOOR_CLOSED,
    CONTROLLER_INPUT_SENSOR_TIMEOUT,
    CONTROLLER_INPUT_INVALID_PRESSURE,
    CONTROLLER_INPUT_INVALID_DOOR,
} controller_input_kind_t;

// Input structure
typedef struct {
    controller_input_kind_t kind;
    int pressure_kpa;
    bool door_closed;
    uint32_t now_ms;
} controller_input_t;

// Controller state structure
typedef struct {
    bool compressor_on;
    bool vent_open;
    controller_state_t state;
    bool has_valid_pressure;
    int last_pressure_kpa;
    uint32_t last_pressure_ms;
    bool has_valid_door;
    bool door_closed;
    uint32_t last_door_ms;
} controller_t;

// Controller output structure
typedef struct {
    bool compressor_on;
    bool vent_open;
    controller_state_t state;
    const char *state_name;
    bool changed;
    bool timed_out;
} controller_output_t;

// Initialize the controller
void controller_init(controller_t *controller);

// Step the controller based on input
controller_output_t controller_step(controller_t *controller, controller_input_t input);

// Get state name for a given state
const char *controller_state_name(controller_state_t state);

#endif // CONTROLLER_H
