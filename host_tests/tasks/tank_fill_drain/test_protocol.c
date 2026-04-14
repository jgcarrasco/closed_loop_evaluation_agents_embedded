#include <stdbool.h>

#include "protocol.h"
#include "test_common.h"

static bool parses_valid_level_frame(void)
{
    protocol_input_t input;
    const protocol_parse_result_t result = protocol_parse_line("SENSE LEVEL 25", &input);

    TEST_ASSERT_INT_EQ(PROTOCOL_PARSE_LEVEL, result);
    TEST_ASSERT_INT_EQ(PROTOCOL_INPUT_LEVEL, input.kind);
    TEST_ASSERT_INT_EQ(25, input.level);
    return true;
}

static bool rejects_malformed_level_value(void)
{
    protocol_input_t input;
    const protocol_parse_result_t result = protocol_parse_line("SENSE LEVEL banana", &input);

    TEST_ASSERT_INT_EQ(PROTOCOL_PARSE_INVALID_LEVEL, result);
    TEST_ASSERT_INT_EQ(PROTOCOL_INPUT_INVALID_LEVEL, input.kind);
    return true;
}

static bool rejects_out_of_range_level(void)
{
    protocol_input_t input;
    const protocol_parse_result_t result = protocol_parse_line("SENSE LEVEL 999", &input);

    TEST_ASSERT_INT_EQ(PROTOCOL_PARSE_INVALID_LEVEL, result);
    TEST_ASSERT_INT_EQ(PROTOCOL_INPUT_INVALID_LEVEL, input.kind);
    return true;
}

static bool ignores_unknown_frame(void)
{
    protocol_input_t input;
    const protocol_parse_result_t result = protocol_parse_line("HELLO WORLD", &input);

    TEST_ASSERT_INT_EQ(PROTOCOL_PARSE_IGNORED, result);
    TEST_ASSERT_INT_EQ(PROTOCOL_INPUT_NONE, input.kind);
    return true;
}

static bool serializes_pump_on_exactly(void)
{
    char buffer[PROTOCOL_MAX_LINE_LENGTH];

    TEST_ASSERT_TRUE(protocol_serialize_act_pump(true, buffer, sizeof(buffer)));
    TEST_ASSERT_STR_EQ("ACT PUMP ON\n", buffer);
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
        {"parse valid SENSE LEVEL 25", parses_valid_level_frame},
        {"reject malformed SENSE LEVEL banana", rejects_malformed_level_value},
        {"reject out-of-range SENSE LEVEL 999", rejects_out_of_range_level},
        {"ignore unknown HELLO WORLD frame", ignores_unknown_frame},
        {"serialize ACT PUMP ON exactly", serializes_pump_on_exactly},
        {"parse FAULT SENSOR_TIMEOUT", parses_sensor_timeout_fault},
    };

    return run_test_cases("protocol", cases, sizeof(cases) / sizeof(cases[0]));
}

