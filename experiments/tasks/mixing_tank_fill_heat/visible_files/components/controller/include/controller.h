#ifndef CONTROLLER_H
#define CONTROLLER_H

#include <stdbool.h>
#include <stdint.h>

#define CONTROLLER_FILL_LEVEL_THRESHOLD 60
#define CONTROLLER_MIN_HEATING_LEVEL 55
#define CONTROLLER_LEVEL_HIGH_THRESHOLD 75
#define CONTROLLER_TEMP_LOW_THRESHOLD 45
#define CONTROLLER_TEMP_EARLY_OFF_THRESHOLD 47
#define CONTROLLER_TEMP_HIGH_THRESHOLD 48
#define CONTROLLER_SENSOR_TIMEOUT_MS 1000U

typedef enum {
    CONTROLLER_INPUT_NONE = 0,
    CONTROLLER_INPUT_TEMPERATURE,
    CONTROLLER_INPUT_LEVEL,
    CONTROLLER_INPUT_SENSOR_TIMEOUT,
    CONTROLLER_INPUT_INVALID_TEMPERATURE,
    CONTROLLER_INPUT_INVALID_LEVEL,
} controller_input_kind_t;

typedef enum {
    CONTROLLER_STATE_SAFE_IDLE = 0,
    CONTROLLER_STATE_FILLING,
    CONTROLLER_STATE_HEATING,
    CONTROLLER_STATE_HOLDING,
} controller_state_t;

typedef struct {
    controller_input_kind_t kind;
    int temperature_c;
    int level;
    uint32_t now_ms;
} controller_input_t;

typedef struct {
    bool inlet_open;
    bool heater_on;
    controller_state_t state;
    bool has_valid_temperature;
    int previous_temperature_c;
    int last_temperature_c;
    uint32_t last_temperature_ms;
    bool has_valid_level;
    int last_level;
    uint32_t last_level_ms;
} controller_t;

typedef struct {
    bool inlet_open;
    bool heater_on;
    controller_state_t state;
    const char *state_name;
    bool changed;
    bool timed_out;
} controller_output_t;

void controller_init(controller_t *controller);
controller_output_t controller_step(controller_t *controller, controller_input_t input);
const char *controller_state_name(controller_state_t state);

#endif
