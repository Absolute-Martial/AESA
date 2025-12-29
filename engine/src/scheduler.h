/**
 * AESA Core Scheduling Engine
 * 
 * C-based constraint satisfaction solver for optimal task scheduling.
 * Implements backtracking algorithm with energy-based heuristics.
 * 
 * Requirements: 2.1, 3.1, 13.1
 */

#ifndef SCHEDULER_H
#define SCHEDULER_H

#include <stdint.h>
#include <stdbool.h>

/* Constants */
#define MAX_TASKS 500
#define MAX_SLOTS 336          /* 7 days * 48 half-hour slots */
#define MAX_NAME_LEN 128
#define MAX_ERROR_LEN 256
#define SLOTS_PER_DAY 48       /* 24 hours * 2 slots per hour */

/* Energy level thresholds */
#define ENERGY_LOW 1
#define ENERGY_MEDIUM 2
#define ENERGY_PEAK 3

/* Priority levels */
#define PRIORITY_FREE_TIME 10
#define PRIORITY_REGULAR_STUDY 50
#define PRIORITY_ASSIGNMENT 60
#define PRIORITY_REVISION_DUE 65
#define PRIORITY_URGENT_LAB 75
#define PRIORITY_EXAM_PREP 85
#define PRIORITY_DUE_TODAY 90
#define PRIORITY_OVERDUE 100

/**
 * Task type enumeration - all 14 supported task types
 * Requirements: 3.1
 */
typedef enum {
    TASK_UNIVERSITY = 0,
    TASK_STUDY = 1,
    TASK_REVISION = 2,
    TASK_PRACTICE = 3,
    TASK_ASSIGNMENT = 4,
    TASK_LAB_WORK = 5,
    TASK_DEEP_WORK = 6,
    TASK_BREAK = 7,
    TASK_FREE_TIME = 8,
    TASK_SLEEP = 9,
    TASK_WAKE_ROUTINE = 10,
    TASK_BREAKFAST = 11,
    TASK_LUNCH = 12,
    TASK_DINNER = 13,
    TASK_TYPE_COUNT = 14
} TaskType;

/**
 * Preferred energy level for task scheduling
 */
typedef enum {
    ENERGY_ANY = 0,
    ENERGY_PREFER_LOW = 1,
    ENERGY_PREFER_MEDIUM = 2,
    ENERGY_PREFER_PEAK = 3
} PreferredEnergy;


/**
 * Task structure - represents a schedulable unit of work
 * Requirements: 2.1
 */
typedef struct {
    int id;                         /* Unique task identifier */
    char name[MAX_NAME_LEN];        /* Task name/title */
    TaskType type;                  /* Type of task */
    int duration_slots;             /* Duration in 30-min slots */
    int priority;                   /* Priority 0-100 */
    int deadline_slot;              /* Deadline slot index, -1 if none */
    bool is_fixed;                  /* True if immutable (class, sleep) */
    PreferredEnergy preferred_energy; /* Preferred energy level */
} Task;

/**
 * TimeSlot structure - represents a 30-minute scheduling unit
 * Requirements: 2.1
 */
typedef struct {
    int slot_index;                 /* Index in the timeline (0 to MAX_SLOTS-1) */
    int task_id;                    /* Assigned task ID, -1 if empty */
    int energy_level;               /* Energy level 1-10 */
    bool is_fixed;                  /* True if slot is fixed/immutable */
} TimeSlot;

/**
 * Timeline structure - represents the complete schedule
 * Requirements: 2.1
 */
typedef struct {
    TimeSlot slots[MAX_SLOTS];      /* Array of time slots */
    int num_slots;                  /* Number of active slots */
    bool success;                   /* True if valid schedule found */
    char error_message[MAX_ERROR_LEN]; /* Error message if failed */
} Timeline;

/**
 * ScheduleInput structure - input for optimization
 */
typedef struct {
    Task* tasks;                    /* Array of tasks to schedule */
    int num_tasks;                  /* Number of tasks */
    TimeSlot* fixed_slots;          /* Pre-fixed slots (classes, etc.) */
    int num_fixed;                  /* Number of fixed slots */
    int num_days;                   /* Number of days to schedule */
} ScheduleInput;

/* ============================================================
 * Memory Management Functions
 * ============================================================ */

/**
 * Allocate a new Task
 * @return Pointer to allocated Task, NULL on failure
 */
Task* task_create(void);

/**
 * Free a Task
 * @param task Pointer to Task to free
 */
void task_free(Task* task);

/**
 * Allocate an array of Tasks
 * @param count Number of tasks to allocate
 * @return Pointer to allocated array, NULL on failure
 */
Task* task_array_create(int count);

/**
 * Free an array of Tasks
 * @param tasks Pointer to task array
 */
void task_array_free(Task* tasks);

/**
 * Allocate a new Timeline
 * @return Pointer to allocated Timeline, NULL on failure
 */
Timeline* timeline_create(void);

/**
 * Free a Timeline
 * @param timeline Pointer to Timeline to free
 */
void timeline_free(Timeline* timeline);

/**
 * Allocate an array of TimeSlots
 * @param count Number of slots to allocate
 * @return Pointer to allocated array, NULL on failure
 */
TimeSlot* timeslot_array_create(int count);

/**
 * Free an array of TimeSlots
 * @param slots Pointer to slot array
 */
void timeslot_array_free(TimeSlot* slots);


/* ============================================================
 * Initialization Functions
 * ============================================================ */

/**
 * Initialize a Task with default values
 * @param task Pointer to Task to initialize
 */
void task_init(Task* task);

/**
 * Initialize a TimeSlot with default values
 * @param slot Pointer to TimeSlot to initialize
 * @param index Slot index in timeline
 */
void timeslot_init(TimeSlot* slot, int index);

/**
 * Initialize a Timeline with default values
 * @param timeline Pointer to Timeline to initialize
 * @param num_days Number of days (determines num_slots)
 */
void timeline_init(Timeline* timeline, int num_days);

/* ============================================================
 * Core Scheduling Functions (implemented in scheduler.c)
 * ============================================================ */

/**
 * Main optimization function - implements backtracking CSP
 * @param tasks Array of tasks to schedule
 * @param num_tasks Number of tasks
 * @param fixed_slots Array of pre-fixed slots
 * @param num_fixed Number of fixed slots
 * @return Optimized Timeline, caller must free with timeline_free()
 * 
 * Requirements: 2.1, 2.2, 2.3, 2.4
 */
Timeline* optimize_schedule(
    Task* tasks,
    int num_tasks,
    TimeSlot* fixed_slots,
    int num_fixed
);

/* ============================================================
 * Utility Functions
 * ============================================================ */

/**
 * Get string name for a TaskType
 * @param type TaskType enum value
 * @return String representation
 */
const char* task_type_to_string(TaskType type);

/**
 * Parse TaskType from string
 * @param str String to parse
 * @return TaskType enum value, or -1 if invalid
 */
int task_type_from_string(const char* str);

/**
 * Get energy level for a given slot index
 * Based on time of day heuristics
 * @param slot_index Index in timeline
 * @return Energy level (1-10)
 */
int get_energy_level(int slot_index);

/**
 * Check if a slot index is in a peak energy period
 * Peak: 8-10am, 4-6pm
 * @param slot_index Index in timeline
 * @return true if peak energy period
 */
bool is_peak_energy_period(int slot_index);

/**
 * Check if a slot index is in a medium energy period
 * Medium: 6-8am, 10am-12pm, 2-4pm, 6-8pm
 * @param slot_index Index in timeline
 * @return true if medium energy period
 */
bool is_medium_energy_period(int slot_index);

/**
 * Check if a slot index is in a low energy period
 * Low: after meals, late evening
 * @param slot_index Index in timeline
 * @return true if low energy period
 */
bool is_low_energy_period(int slot_index);

/**
 * Compare tasks by priority (for sorting)
 * @param a First task
 * @param b Second task
 * @return Negative if a > b priority, positive if a < b, 0 if equal
 */
int task_compare_priority(const void* a, const void* b);

#endif /* SCHEDULER_H */
