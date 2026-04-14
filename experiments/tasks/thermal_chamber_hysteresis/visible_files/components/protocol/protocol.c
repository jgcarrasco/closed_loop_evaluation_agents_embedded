#include "protocol.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void protocol_reset_input(protocol_input_t *input)
{
    if (input == NULL) {
        return;
    }

    input->kind = PROTOCOL_INPUT_NONE;
    input->temperature_c = 0;
}

static void protocol_trim_copy(const char *line, char *buffer, size_t buffer_size)
{
    size_t source_length;
    size_t start = 0U;
    size_t end;
    size_t length;

    if (buffer_size == 0U) {
        return;
    }

    buffer[0] = '\0';
    if (line == NULL) {
        return;
    }

    source_length = strnlen(line, buffer_size - 1U);
    while ((start < source_length) && isspace((unsigned char) line[start])) {
        start++;
    }

    end = source_length;
    while ((end > start) && isspace((unsigned char) line[end - 1U])) {
        end--;
    }

    length = end - start;
    memcpy(buffer, line + start, length);
    buffer[length] = '\0';
}

static bool protocol_parse_temperature_value(const char *token, int *temperature_c)
{
    char *end = NULL;
    long parsed;

    if ((token == NULL) || (temperature_c == NULL)) {
        return false;
    }

    parsed = strtol(token, &end, 10);
    if ((end == token) || (*end != '\0')) {
        return false;
    }

    if ((parsed < 15L) || (parsed > 80L)) {
        return false;
    }

    *temperature_c = (int) parsed;
    return true;
}

protocol_parse_result_t protocol_parse_line(const char *line, protocol_input_t *input)
{
    char scratch[PROTOCOL_MAX_LINE_LENGTH];
    char *save = NULL;
    char *first;
    char *second;
    char *third;
    char *fourth;
    int temperature_c;

    protocol_reset_input(input);
    protocol_trim_copy(line, scratch, sizeof(scratch));
    if (scratch[0] == '\0') {
        return PROTOCOL_PARSE_IGNORED;
    }

    first = strtok_r(scratch, " \t", &save);
    second = strtok_r(NULL, " \t", &save);
    third = strtok_r(NULL, " \t", &save);
    fourth = strtok_r(NULL, " \t", &save);

    if ((first != NULL) && (second != NULL) && (strcmp(first, "SENSE") == 0) && (strcmp(second, "TEMP") == 0)) {
        if ((third == NULL) || (fourth != NULL) || !protocol_parse_temperature_value(third, &temperature_c)) {
            if (input != NULL) {
                input->kind = PROTOCOL_INPUT_INVALID_TEMPERATURE;
            }
            return PROTOCOL_PARSE_INVALID_TEMPERATURE;
        }

        if (input != NULL) {
            input->kind = PROTOCOL_INPUT_TEMPERATURE;
            input->temperature_c = temperature_c;
        }
        return PROTOCOL_PARSE_TEMPERATURE;
    }

    if ((first != NULL) && (second != NULL) && (strcmp(first, "FAULT") == 0) && (strcmp(second, "SENSOR_TIMEOUT") == 0) && (third == NULL)) {
        if (input != NULL) {
            input->kind = PROTOCOL_INPUT_SENSOR_TIMEOUT;
        }
        return PROTOCOL_PARSE_SENSOR_TIMEOUT;
    }

    return PROTOCOL_PARSE_IGNORED;
}

bool protocol_serialize_act_heater(bool heater_on, char *buffer, size_t buffer_size)
{
    const int written = snprintf(buffer, buffer_size, "ACT HEATER %s\n", heater_on ? "ON" : "OFF");
    return (written >= 0) && ((size_t) written < buffer_size);
}

bool protocol_serialize_debug(const char *message, char *buffer, size_t buffer_size)
{
    const int written = snprintf(buffer, buffer_size, "DBG %s\n", message != NULL ? message : "");
    return (written >= 0) && ((size_t) written < buffer_size);
}

