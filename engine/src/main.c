/**
 * AESA Core Scheduling Engine - Main Entry Point
 * 
 * Reads JSON input from stdin, runs optimization, outputs JSON to stdout.
 * 
 * Usage: ./scheduler < input.json > output.json
 */

#include "scheduler.h"
#include "json_output.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_INPUT_SIZE (1024 * 1024)  /* 1MB max input */

int main(int argc, char* argv[]) {
    (void)argc;  /* Unused */
    (void)argv;  /* Unused */
    
    /* Read JSON input from stdin */
    char* input = (char*)malloc(MAX_INPUT_SIZE);
    if (input == NULL) {
        fprintf(stderr, "{\"success\": false, \"error_message\": \"Memory allocation failed\"}\n");
        return 1;
    }
    
    size_t total_read = 0;
    size_t bytes_read;
    
    while ((bytes_read = fread(input + total_read, 1, MAX_INPUT_SIZE - total_read - 1, stdin)) > 0) {
        total_read += bytes_read;
        if (total_read >= MAX_INPUT_SIZE - 1) break;
    }
    input[total_read] = '\0';
    
    /* Parse input */
    Task* tasks = NULL;
    int num_tasks = 0;
    TimeSlot* fixed_slots = NULL;
    int num_fixed = 0;
    
    if (parse_json_input(input, &tasks, &num_tasks, &fixed_slots, &num_fixed) != 0) {
        fprintf(stderr, "{\"success\": false, \"error_message\": \"Failed to parse input JSON\"}\n");
        free(input);
        return 1;
    }
    
    free(input);
    
    /* Run optimization */
    Timeline* timeline = optimize_schedule(tasks, num_tasks, fixed_slots, num_fixed);
    
    /* Cleanup input data */
    if (tasks) task_array_free(tasks);
    if (fixed_slots) timeslot_array_free(fixed_slots);
    
    if (timeline == NULL) {
        fprintf(stderr, "{\"success\": false, \"error_message\": \"Optimization failed\"}\n");
        return 1;
    }
    
    /* Output result as JSON */
    char* json_output = timeline_to_json(timeline);
    timeline_free(timeline);
    
    if (json_output == NULL) {
        fprintf(stderr, "{\"success\": false, \"error_message\": \"JSON serialization failed\"}\n");
        return 1;
    }
    
    printf("%s", json_output);
    free_json(json_output);
    
    return 0;
}
