# AESA Core Scheduling Engine - Makefile
# Requirements: 20.1, 20.4

CC = gcc
CFLAGS = -std=c99 -Wall -Wextra -Werror -pedantic -O2
LDFLAGS = -lm

# Debug build flags
DEBUG_CFLAGS = -std=c99 -Wall -Wextra -g -O0 -DDEBUG

# Source files
SRC_DIR = src
TEST_DIR = tests
BUILD_DIR = build

SRCS = $(SRC_DIR)/scheduler.c $(SRC_DIR)/json_output.c
MAIN_SRC = $(SRC_DIR)/main.c
TEST_SRCS = $(wildcard $(TEST_DIR)/*.c)

OBJS = $(SRCS:.c=.o)
MAIN_OBJ = $(MAIN_SRC:.c=.o)

# Output binary
TARGET = scheduler
TEST_TARGET = scheduler_test

# Default target
all: $(TARGET)

# Main scheduler binary
$(TARGET): $(OBJS) $(MAIN_OBJ)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Object files
%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

# Debug build
debug: CFLAGS = $(DEBUG_CFLAGS)
debug: clean $(TARGET)

# Test build
test: $(TEST_TARGET)
	./$(TEST_TARGET)

$(TEST_TARGET): $(OBJS) $(TEST_SRCS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Clean build artifacts
clean:
	rm -f $(SRC_DIR)/*.o $(TEST_DIR)/*.o $(TARGET) $(TEST_TARGET)
	rm -rf $(BUILD_DIR)

# Install (copy to /usr/local/bin)
install: $(TARGET)
	cp $(TARGET) /usr/local/bin/

# Uninstall
uninstall:
	rm -f /usr/local/bin/$(TARGET)

# Memory check with valgrind
memcheck: debug
	valgrind --leak-check=full --show-leak-kinds=all ./$(TARGET) < tests/sample_input.json

# Format check (requires clang-format)
format:
	clang-format -i $(SRC_DIR)/*.c $(SRC_DIR)/*.h

# Static analysis (requires cppcheck)
analyze:
	cppcheck --enable=all --std=c99 $(SRC_DIR)

.PHONY: all debug test clean install uninstall memcheck format analyze
