/**
 * AESA Core Scheduling Engine - JSON Output
 * 
 * JSON serialization for Timeline and related structures.
 * 
 * Requirements: 2.6
 */

#ifndef JSON_OUTPUT_H
#define JSON_OUTPUT_H

#include "scheduler.h"

/**
 * Serialize a Timeline to JSON string
 * @param timeline Timeline to serialize
 * @return JSON string, caller must free with free_json()
 */
char* timeline_to_json(Timeline* timeline);

/**
 * Free JSON string allocated by timeline_to_json
 * @param json JSON string to free
 */
void free_json(char* json);

/**
 * Parse JSON input to create tasks and fixed slots
 * @param json_input JSON string input
 * @param tasks Output: array of tasks (caller must free)
 * @param num_tasks Output: number of tasks
 * @param fixed_slots Output: array of fixed slots (caller must free)
 * @param num_fixed Output: number of fixed slots
 * @return 0 on success, -1 on error
 */
int parse_json_input(
    const char* json_input,
    Task** tasks,
    int* num_tasks,
    TimeSlot** fixed_slots,
    int* num_fixed
);

#endif /* JSON_OUTPUT_H */
