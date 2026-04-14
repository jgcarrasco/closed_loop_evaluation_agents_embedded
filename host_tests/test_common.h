#ifndef HOST_TEST_COMMON_H
#define HOST_TEST_COMMON_H

#include <stdbool.h>
#include <stdio.h>
#include <string.h>

typedef bool (*test_fn_t)(void);

typedef struct {
    const char *name;
    test_fn_t fn;
} test_case_t;

static inline const char *test_display_path(const char *path)
{
    const char *host_tests_path = strstr(path, "/host_tests/");
    const char *slash = strrchr(path, '/');

    if (host_tests_path != NULL) {
        return host_tests_path + 1;
    }
    if (slash != NULL) {
        return slash + 1;
    }
    return path;
}

static inline int run_test_cases(const char *suite_name, const test_case_t *cases, size_t count)
{
    size_t index;
    int failures = 0;

    for (index = 0U; index < count; ++index) {
        const bool passed = cases[index].fn();
        fprintf(stdout, "[%s] %s: %s\n", suite_name, cases[index].name, passed ? "PASS" : "FAIL");
        if (!passed) {
            failures++;
        }
    }

    return failures;
}

#define TEST_ASSERT_TRUE(expr) \
    do { \
        if (!(expr)) { \
            fprintf(stderr, "Assertion failed at %s:%d: %s\n", test_display_path(__FILE__), __LINE__, #expr); \
            return false; \
        } \
    } while (0)

#define TEST_ASSERT_FALSE(expr) TEST_ASSERT_TRUE(!(expr))
#define TEST_ASSERT_INT_EQ(expected, actual) TEST_ASSERT_TRUE((expected) == (actual))
#define TEST_ASSERT_STR_EQ(expected, actual) TEST_ASSERT_TRUE(strcmp((expected), (actual)) == 0)

int run_controller_tests(void);
int run_protocol_tests(void);

#endif
