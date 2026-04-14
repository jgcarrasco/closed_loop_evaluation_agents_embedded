#include <stdbool.h>

#include "protocol.h"
#include "test_common.h"

static bool parses_valid_pressure_frame(void)
{
    protocol_input_t input;
    const protocol_parse_result_t result = protocol_parse_line("SENSE PRESS 42", &input);

    TEST_ASSERT_INT_EQ(PROTOCOL_PARSE_PRESSURE, result);
    TEST_ASSERT_INT_EQ(PROTOCOL_INPUT_PRESSURE, input.kind);
    TEST_ASSERT_INT_EQ(42, input.pressure_kpa);
    return true;
}

static bool parses_valid_door_frame(void)
{
    protocol_input_t input;
    const protocol_parse_result_t result = protocol_parse_line("SENSE DOOR OPEN", &input);

    TEST_ASSERT_INT_EQ(PROTOCOL_PARSE_DOOR_OPEN, result);
    TEST_ASSERT_INT_EQ(PROTOCOL_INPUT_DOOR_OPEN, input.kind);
    TEST_ASSERT_FALSE(input.door_closed);
    return true;
}

static bool rejects_invalid_pressure_value(void)
{
    protocol_input_t input;
    const protocol_parse_result_t result = protocol_parse_line("SENSE PRESS banana", &input);

    TEST_ASSERT_INT_EQ(PROTOCOL_PARSE_INVALID_PRESSURE, result);
    TEST_ASSERT_INT_EQ(PROTOCOL_INPUT_INVALID_PRESSURE, input.kind);
    return true;
}

static bool rejects_invalid_door_value(void)
{
    protocol_input_t input;
    const protocol_parse_result_t result = protocol_parse_line("SENSE DOOR AJAR", &input);

    TEST_ASSERT_INT_EQ(PROTOCOL_PARSE_INVALID_DOOR, result);
    TEST_ASSERT_INT_EQ(PROTOCOL_INPUT_INVALID_DOOR, input.kind);
    return true;
}

static bool serializes_compressor_on_exactly(void)
{
    char buffer[PROTOCOL_MAX_LINE_LENGTH];

    TEST_ASSERT_TRUE(protocol_serialize_act_compressor(true, buffer, sizeof(buffer)));
    TEST_ASSERT_STR_EQ("ACT COMPRESSOR ON\n", buffer);
    return true;
}

static bool serializes_vent_open_exactly(void)
{
    char buffer[PROTOCOL_MAX_LINE_LENGTH];

    TEST_ASSERT_TRUE(protocol_serialize_act_vent(true, buffer, sizeof(buffer)));
    TEST_ASSERT_STR_EQ("ACT VENT OPEN\n", buffer);
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
        {"parse valid SENSE PRESS 42", parses_valid_pressure_frame},
        {"parse valid SENSE DOOR OPEN", parses_valid_door_frame},
        {"reject invalid pressure value", rejects_invalid_pressure_value},
        {"reject invalid door value", rejects_invalid_door_value},
        {"serialize ACT COMPRESSOR ON exactly", serializes_compressor_on_exactly},
        {"serialize ACT VENT OPEN exactly", serializes_vent_open_exactly},
        {"parse FAULT SENSOR_TIMEOUT", parses_sensor_timeout_fault},
    };

    return run_test_cases("protocol", cases, sizeof(cases) / sizeof(cases[0]));
}
