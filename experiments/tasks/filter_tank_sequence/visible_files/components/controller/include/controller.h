#ifndef CONTROLLER_H
#define CONTROLLER_H

#include <stdbool.h>
#include <stdint.h>

#define CONTROLLER_CLEAR_THRESHOLD_NTU 35
#define CONTROLLER_SETTLING_RESET_THRESHOLD_NTU 40
#define CONTROLLER_DRAINING_DISTURBANCE_THRESHOLD_NTU 50
#define CONTROLLER_MIN_PROCESS_LEVEL 40
#define CONTROLLER_COMPLETE_LEVEL 15
#define CONTROLLER_CLEAR_STREAK_REQUIRED 3
#define CONTROLLER_SETTLING_MS 400U
#define CONTROLLER_SENSOR_TIMEOUT_MS 1000U

typedef enum {
    CONTROLLER_INPUT_NONE = 0,
    CONTROLLER_INPUT_TURBIDITY,
    CONTROLLER_INPUT_LEVEL,
    CONTROLLER_INPUT_SENSOR_TIMEOUT,
    CONTROLLER_INPUT_INVALID_TURBIDITY,
    CONTROLLER_INPUT_INVALID_LEVEL,
} controller_input_kind_t;

typedef enum {
    CONTROLLER_STATE_SAFE_IDLE = 0,
    CONTROLLER_STATE_FILTERING,
    CONTROLLER_STATE_SETTLING,
    CONTROLLER_STATE_DRAINING,
    CONTROLLER_STATE_COMPLETE,
} controller_state_t;

typedef struct {
    controller_input_kind_t kind;
    int turbidity_ntu;
    int level;
    uint32_t now_ms;
} controller_input_t;

typedef struct {
    bool filter_on;
    bool drain_open;
    controller_state_t state;
    bool has_valid_turbidity;
    int last_turbidity_ntu;
    uint32_t last_turbidity_ms;
    bool has_valid_level;
    int last_level;
    uint32_t last_level_ms;
    int clear_streak_count;
    uint32_t settling_started_ms;
} controller_t;

typedef struct {
    bool filter_on;
    bool drain_open;
    controller_state_t state;
    const char *state_name;
    bool changed;
    bool timed_out;
} controller_output_t;

void controller_init(controller_t *controller);
controller_output_t controller_step(controller_t *controller, controller_input_t input);
const char *controller_state_name(controller_state_t state);

#endif
