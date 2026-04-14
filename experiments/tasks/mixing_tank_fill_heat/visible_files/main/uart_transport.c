#include "uart_transport.h"

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "controller.h"
#include "driver/uart.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "protocol.h"

#define UART_TRANSPORT_PORT UART_NUM_0
#define UART_TRANSPORT_BAUDRATE 115200
#define UART_TRANSPORT_BUFFER_SIZE 256
#define UART_TRANSPORT_LINE_BUFFER_SIZE 128
#define UART_TRANSPORT_HEARTBEAT_MS 1000U
#define UART_TRANSPORT_POLL_MS 50U

typedef struct {
    controller_t controller;
    char rx_line[UART_TRANSPORT_LINE_BUFFER_SIZE];
    size_t rx_line_length;
} uart_transport_context_t;

static uart_transport_context_t s_transport_context;

static uint32_t transport_now_ms(void)
{
    return (uint32_t) (xTaskGetTickCount() * portTICK_PERIOD_MS);
}

static void transport_send_line(const char *line)
{
    if (line == NULL) {
        return;
    }

    uart_write_bytes(UART_TRANSPORT_PORT, line, strlen(line));
}

static void transport_send_debug(const char *message)
{
    char buffer[PROTOCOL_MAX_LINE_LENGTH];
    if (protocol_serialize_debug(message, buffer, sizeof(buffer))) {
        transport_send_line(buffer);
    }
}

static void transport_send_actuators(bool inlet_open, bool heater_on)
{
    char buffer[PROTOCOL_MAX_LINE_LENGTH];
    if (protocol_serialize_act_inlet(inlet_open, buffer, sizeof(buffer))) {
        transport_send_line(buffer);
    }
    if (protocol_serialize_act_heater(heater_on, buffer, sizeof(buffer))) {
        transport_send_line(buffer);
    }
}

static void transport_apply_protocol_input(const protocol_input_t *protocol_input)
{
    controller_input_t controller_input = {
        .kind = CONTROLLER_INPUT_NONE,
        .temperature_c = 0,
        .level = 0,
        .now_ms = transport_now_ms(),
    };

    if (protocol_input == NULL) {
        return;
    }

    switch (protocol_input->kind) {
    case PROTOCOL_INPUT_TEMPERATURE:
        controller_input.kind = CONTROLLER_INPUT_TEMPERATURE;
        controller_input.temperature_c = protocol_input->temperature_c;
        break;
    case PROTOCOL_INPUT_LEVEL:
        controller_input.kind = CONTROLLER_INPUT_LEVEL;
        controller_input.level = protocol_input->level;
        break;
    case PROTOCOL_INPUT_SENSOR_TIMEOUT:
        controller_input.kind = CONTROLLER_INPUT_SENSOR_TIMEOUT;
        break;
    case PROTOCOL_INPUT_INVALID_TEMPERATURE:
        controller_input.kind = CONTROLLER_INPUT_INVALID_TEMPERATURE;
        break;
    case PROTOCOL_INPUT_INVALID_LEVEL:
        controller_input.kind = CONTROLLER_INPUT_INVALID_LEVEL;
        break;
    case PROTOCOL_INPUT_NONE:
    default:
        controller_input.kind = CONTROLLER_INPUT_NONE;
        break;
    }

    controller_output_t output = controller_step(&s_transport_context.controller, controller_input);
    if (output.changed || controller_input.kind != CONTROLLER_INPUT_NONE) {
        transport_send_actuators(output.inlet_open, output.heater_on);
        transport_send_debug(output.state_name);
    }
}

static void transport_handle_received_line(const char *line)
{
    protocol_input_t input = {
        .kind = PROTOCOL_INPUT_NONE,
        .temperature_c = 0,
        .level = 0,
    };

    protocol_parse_result_t result = protocol_parse_line(line, &input);
    if (result == PROTOCOL_PARSE_IGNORED) {
        return;
    }

    transport_apply_protocol_input(&input);
}

static void transport_poll_controller_timeout(void)
{
    controller_input_t controller_input = {
        .kind = CONTROLLER_INPUT_NONE,
        .temperature_c = 0,
        .level = 0,
        .now_ms = transport_now_ms(),
    };

    controller_output_t output = controller_step(&s_transport_context.controller, controller_input);
    if (output.changed) {
        transport_send_actuators(output.inlet_open, output.heater_on);
        transport_send_debug(output.state_name);
    }
}

static void transport_consume_uart_bytes(const uint8_t *bytes, size_t length)
{
    size_t index = 0;

    while (index < length) {
        const char current = (char) bytes[index++];
        if (current == '\r') {
            continue;
        }

        if (current == '\n') {
            s_transport_context.rx_line[s_transport_context.rx_line_length] = '\0';
            if (s_transport_context.rx_line_length > 0U) {
                transport_handle_received_line(s_transport_context.rx_line);
            }
            s_transport_context.rx_line_length = 0U;
            continue;
        }

        if (s_transport_context.rx_line_length + 1U < sizeof(s_transport_context.rx_line)) {
            s_transport_context.rx_line[s_transport_context.rx_line_length++] = current;
        } else {
            s_transport_context.rx_line_length = 0U;
            transport_send_debug("RX_LINE_TOO_LONG");
        }
    }
}

static void transport_task(void *unused)
{
    uint8_t buffer[UART_TRANSPORT_BUFFER_SIZE];
    uint32_t next_heartbeat_ms;

    (void) unused;

    transport_send_debug("BOOTED");
    transport_send_actuators(false, false);
    transport_send_debug("STATE SAFE_IDLE");
    next_heartbeat_ms = transport_now_ms() + UART_TRANSPORT_HEARTBEAT_MS;

    while (true) {
        const int bytes_read = uart_read_bytes(
            UART_TRANSPORT_PORT,
            buffer,
            sizeof(buffer),
            pdMS_TO_TICKS(UART_TRANSPORT_POLL_MS)
        );

        if (bytes_read > 0) {
            transport_consume_uart_bytes(buffer, (size_t) bytes_read);
        }

        transport_poll_controller_timeout();

        if (transport_now_ms() < next_heartbeat_ms) {
            continue;
        }

        transport_send_debug("HEARTBEAT");
        next_heartbeat_ms = transport_now_ms() + UART_TRANSPORT_HEARTBEAT_MS;
    }
}

void uart_transport_start(void)
{
    controller_init(&s_transport_context.controller);
    s_transport_context.rx_line_length = 0U;

    uart_config_t config = {
        .baud_rate = UART_TRANSPORT_BAUDRATE,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_APB,
    };

    uart_driver_install(UART_TRANSPORT_PORT, UART_TRANSPORT_BUFFER_SIZE * 2, 0, 0, NULL, 0);
    uart_param_config(UART_TRANSPORT_PORT, &config);
    uart_set_pin(UART_TRANSPORT_PORT, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);

    xTaskCreate(transport_task, "uart_transport", 4096, NULL, 5, NULL);
}
