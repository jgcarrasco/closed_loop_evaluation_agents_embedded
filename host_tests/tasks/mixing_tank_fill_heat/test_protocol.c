#include <stdbool.h>

#include "protocol.h"
#include "test_common.h"

static bool parses_valid_temp_frame(void)
{
    protocol_input_t input;
    const protocol_parse_result_t result = protocol_parse_line("SENSE TEMP 42", &input);

    TEST_ASSERT_INT_EQ(PROTOCOL_PARSE_TEMPERATURE, result);
    TEST_ASSERT_INT_EQ(PROTOCOL_INPUT_TEMPERATURE, input.kind);
    TEST_ASSERT_INT_EQ(42, input.temperature_c);
    return true;
}

static bool parses_valid_level_frame(void)
{
    protocol_input_t input;
    const protocol_parse_result_t result = protocol_parse_line("SENSE LEVEL 67", &input);

    TEST_ASSERT_INT_EQ(PROTOCOL_PARSE_LEVEL, result);
    TEST_ASSERT_INT_EQ(PROTOCOL_INPUT_LEVEL, input.kind);
    TEST_ASSERT_INT_EQ(67, input.level);
    return true;
}

static bool rejects_invalid_temp_value(void)
{
    protocol_input_t input;
    const protocol_parse_result_t result = protocol_parse_line("SENSE TEMP banana", &input);

    TEST_ASSERT_INT_EQ(PROTOCOL_PARSE_INVALID_TEMPERATURE, result);
    TEST_ASSERT_INT_EQ(PROTOCOL_INPUT_INVALID_TEMPERATURE, input.kind);
    return true;
}

static bool rejects_invalid_level_value(void)
{
    protocol_input_t input;
    const protocol_parse_result_t result = protocol_parse_line("SENSE LEVEL -1", &input);

    TEST_ASSERT_INT_EQ(PROTOCOL_PARSE_INVALID_LEVEL, result);
    TEST_ASSERT_INT_EQ(PROTOCOL_INPUT_INVALID_LEVEL, input.kind);
    return true;
}

static bool serializes_inlet_open_exactly(void)
{
    char buffer[PROTOCOL_MAX_LINE_LENGTH];

    TEST_ASSERT_TRUE(protocol_serialize_act_inlet(true, buffer, sizeof(buffer)));
    TEST_ASSERT_STR_EQ("ACT INLET OPEN\n", buffer);
    return true;
}

static bool serializes_heater_on_exactly(void)
{
    char buffer[PROTOCOL_MAX_LINE_LENGTH];

    TEST_ASSERT_TRUE(protocol_serialize_act_heater(true, buffer, sizeof(buffer)));
    TEST_ASSERT_STR_EQ("ACT HEATER ON\n", buffer);
    return true;
}

static bool parses_sensor_timeout_fault(void)
{
    protocol_input_t input;
    const protocol_parse_result_t result = protocol_parse_line("FAULT SENSOR_TIMEOUT", &input);

    TEST_ASSERT_INT_EQ(PROTOCOL_PARSE_SENSOR_TIMEOUT, result);
    TEST_ASSERT_INT_EQ(PROTOCOL_INPUT_SENSOR_TIMEOUT, input.kind);
    return true;
}

int run_protocol_tests(void)
{
    const test_case_t cases[] = {
        {"parse valid SENSE TEMP 42", parses_valid_temp_frame},
        {"parse valid SENSE LEVEL 67", parses_valid_level_frame},
        {"reject invalid temp value", rejects_invalid_temp_value},
        {"reject invalid level value", rejects_invalid_level_value},
        {"serialize ACT INLET OPEN exactly", serializes_inlet_open_exactly},
        {"serialize ACT HEATER ON exactly", serializes_heater_on_exactly},
        {"parse FAULT SENSOR_TIMEOUT", parses_sensor_timeout_fault},
    };

    return run_test_cases("protocol", cases, sizeof(cases) / sizeof(cases[0]));
}
