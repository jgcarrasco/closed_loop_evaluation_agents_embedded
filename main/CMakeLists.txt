idf_component_register(
    SRCS
        "app_main.c"
        "uart_transport.c"
    INCLUDE_DIRS
        "."
    REQUIRES
        controller
        protocol
        driver
)

