#include <stdio.h>

#include "test_common.h"

int main(void)
{
    int failures = 0;

    failures += run_protocol_tests();
    failures += run_controller_tests();

    if (failures == 0) {
        fprintf(stdout, "All host tests passed.\n");
    }

    return failures == 0 ? 0 : 1;
}

