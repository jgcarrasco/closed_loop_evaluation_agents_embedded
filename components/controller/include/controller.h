#ifndef CONTROLLER_H
#define CONTROLLER_H

#include <stdbool.h>
#include <stdint.h>

#define CONTROLLER_LEVEL_LOW_THRESHOLD 30
#define CONTROLLER_LEVEL_HIGH_THRESHOLD 80
#define CONTROLLER_SENSOR_TIMEOUT_MS 1000U

typedef enum {
    CONTROLLER_INPUT_NONE = 0,
    CONTROLLER_INPUT_LEVEL,
    CONTROLLER_INPUT_SENSOR_TIMEOUT,
    CONTROLLER_INPUT_INVALID_LEVEL,
} controller_input_kind_t;

typedef enum {
    CONTROLLER_STATE_SAFE_OFF = 0,
    CONTROLLER_STATE_PUMPING,
    CONTROLLER_STATE_HOLDING,
} controller_state_t;

typedef struct {
    controller_input_kind_t kind;
    int level;
    uint32_t now_ms;
} controller_input_t;

typedef struct {
    bool pump_on;
    controller_state_t state;
    bool has_valid_sensor;
    int last_level;
    uint32_t last_valid_sensor_ms;
} controller_t;

typedef struct {
    bool pump_on;
    controller_state_t state;
    const char *state_name;
    bool changed;
    bool timed_out;
} controller_output_t;

void controller_init(controller_t *controller);
controller_output_t controller_step(controller_t *controller, controller_input_t input);
const char *controller_state_name(controller_state_t state);

#endif
