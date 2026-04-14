#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stdbool.h>
#include <stddef.h>

#define PROTOCOL_MAX_LINE_LENGTH 128

typedef enum {
    PROTOCOL_INPUT_NONE = 0,
    PROTOCOL_INPUT_TEMPERATURE,
    PROTOCOL_INPUT_SENSOR_TIMEOUT,
    PROTOCOL_INPUT_INVALID_TEMPERATURE,
} protocol_input_kind_t;

typedef struct {
    protocol_input_kind_t kind;
    int temperature_c;
} protocol_input_t;

typedef enum {
    PROTOCOL_PARSE_IGNORED = 0,
    PROTOCOL_PARSE_TEMPERATURE,
    PROTOCOL_PARSE_SENSOR_TIMEOUT,
    PROTOCOL_PARSE_INVALID_TEMPERATURE,
} protocol_parse_result_t;

protocol_parse_result_t protocol_parse_line(const char *line, protocol_input_t *input);
bool protocol_serialize_act_heater(bool heater_on, char *buffer, size_t buffer_size);
bool protocol_serialize_debug(const char *message, char *buffer, size_t buffer_size);

#endif

