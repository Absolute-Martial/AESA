/**
 * AESA Core Scheduling Engine - Implementation
 * 
 * Implements constraint satisfaction solver with backtracking algorithm.
 * 
 * Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 4.2
 */

#include "scheduler.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/* ============================================================
 * Task Type String Mapping
 * ============================================================ */

static const char* TASK_TYPE_STRINGS[] = {
    "university",
    "study",
    "revision",
    "practice",
    "assignment",
    "lab_work",
    "deep_work",
    "break",
    "free_time",
    "sleep",
    "wake_routine",
    "breakfast",
    "lunch",
    "dinner"
};

const char* task_type_to_string(TaskType type) {
    if (type >= 0 && type < TASK_TYPE_COUNT) {
        return TASK_TYPE_STRINGS[type];
    }
    return "unknown";
}

int task_type_from_string(const char* str) {
    if (str == NULL) return -1;
    
    for (int i = 0; i < TASK_TYPE_COUNT; i++) {
        if (strcmp(str, TASK_TYPE_STRINGS[i]) == 0) {
            return i;
        }
    }
    return -1;
}


/* ============================================================
 * Memory Management Functions
 * ============================================================ */

Task* task_create(void) {
    Task* task = (Task*)malloc(sizeof(Task));
    if (task != NULL) {
        task_init(task);
    }
    return task;
}

void task_free(Task* task) {
    if (task != NULL) {
        free(task);
    }
}

Task* task_array_create(int count) {
    if (count <= 0 || count > MAX_TASKS) {
        return NULL;
    }
    
    Task* tasks = (Task*)malloc(sizeof(Task) * count);
    if (tasks != NULL) {
        for (int i = 0; i < count; i++) {
            task_init(&tasks[i]);
        }
    }
    return tasks;
}

void task_array_free(Task* tasks) {
    if (tasks != NULL) {
        free(tasks);
    }
}

Timeline* timeline_create(void) {
    Timeline* timeline = (Timeline*)malloc(sizeof(Timeline));
    if (timeline != NULL) {
        timeline_init(timeline, 7); /* Default to 7 days */
    }
    return timeline;
}

void timeline_free(Timeline* timeline) {
    if (timeline != NULL) {
        free(timeline);
    }
}

TimeSlot* timeslot_array_create(int count) {
    if (count <= 0 || count > MAX_SLOTS) {
        return NULL;
    }
    
    TimeSlot* slots = (TimeSlot*)malloc(sizeof(TimeSlot) * count);
    if (slots != NULL) {
        for (int i = 0; i < count; i++) {
            timeslot_init(&slots[i], i);
        }
    }
    return slots;
}

void timeslot_array_free(TimeSlot* slots) {
    if (slots != NULL) {
        free(slots);
    }
}

/* ============================================================
 * Initialization Functions
 * ============================================================ */

void task_init(Task* task) {
    if (task == NULL) return;
    
    task->id = -1;
    task->name[0] = '\0';
    task->type = TASK_STUDY;
    task->duration_slots = 1;
    task->priority = PRIORITY_REGULAR_STUDY;
    task->deadline_slot = -1;
    task->is_fixed = false;
    task->preferred_energy = ENERGY_ANY;
}

void timeslot_init(TimeSlot* slot, int index) {
    if (slot == NULL) return;
    
    slot->slot_index = index;
    slot->task_id = -1;
    slot->energy_level = get_energy_level(index);
    slot->is_fixed = false;
}

void timeline_init(Timeline* timeline, int num_days) {
    if (timeline == NULL) return;
    
    int total_slots = num_days * SLOTS_PER_DAY;
    if (total_slots > MAX_SLOTS) {
        total_slots = MAX_SLOTS;
    }
    
    timeline->num_slots = total_slots;
    timeline->success = false;
    timeline->error_message[0] = '\0';
    
    for (int i = 0; i < total_slots; i++) {
        timeslot_init(&timeline->slots[i], i);
    }
}


/* ============================================================
 * Energy Level Functions
 * Requirements: 3.2, 3.3, 3.4
 * ============================================================ */

/**
 * Get hour of day from slot index (0-23)
 */
static int slot_to_hour(int slot_index) {
    int slot_in_day = slot_index % SLOTS_PER_DAY;
    return slot_in_day / 2; /* 2 slots per hour */
}

int get_energy_level(int slot_index) {
    int hour = slot_to_hour(slot_index);
    
    /* Peak energy: 8-10am, 4-6pm -> energy 8-10 */
    if ((hour >= 8 && hour < 10) || (hour >= 16 && hour < 18)) {
        return 9;
    }
    
    /* Medium energy: 6-8am, 10am-12pm, 2-4pm, 6-8pm -> energy 5-7 */
    if ((hour >= 6 && hour < 8) || 
        (hour >= 10 && hour < 12) ||
        (hour >= 14 && hour < 16) ||
        (hour >= 18 && hour < 20)) {
        return 6;
    }
    
    /* Low energy: after meals (12-2pm), late evening (8pm+), early morning */
    if ((hour >= 12 && hour < 14) || hour >= 20 || hour < 6) {
        return 3;
    }
    
    /* Default medium */
    return 5;
}

bool is_peak_energy_period(int slot_index) {
    int hour = slot_to_hour(slot_index);
    return (hour >= 8 && hour < 10) || (hour >= 16 && hour < 18);
}

bool is_medium_energy_period(int slot_index) {
    int hour = slot_to_hour(slot_index);
    return (hour >= 6 && hour < 8) || 
           (hour >= 10 && hour < 12) ||
           (hour >= 14 && hour < 16) ||
           (hour >= 18 && hour < 20);
}

bool is_low_energy_period(int slot_index) {
    int hour = slot_to_hour(slot_index);
    return (hour >= 12 && hour < 14) || hour >= 20 || hour < 6;
}

/* ============================================================
 * Priority Comparison
 * Requirements: 4.2
 * ============================================================ */

int task_compare_priority(const void* a, const void* b) {
    const Task* task_a = (const Task*)a;
    const Task* task_b = (const Task*)b;
    
    /* Higher priority first (descending order) */
    return task_b->priority - task_a->priority;
}


/* ============================================================
 * Constraint Checking Functions
 * Requirements: 2.1, 2.2, 2.3, 2.4
 * ============================================================ */

/**
 * Check if a slot is available (not occupied and not fixed)
 */
static bool is_slot_available(Timeline* timeline, int slot_index) {
    if (slot_index < 0 || slot_index >= timeline->num_slots) {
        return false;
    }
    return timeline->slots[slot_index].task_id == -1 && 
           !timeline->slots[slot_index].is_fixed;
}

/**
 * Check if task can be placed at given slot (all constraints)
 * - No overlap with existing tasks
 * - Not in fixed slots
 * - Before deadline if applicable
 * - Enough consecutive slots for duration
 */
static bool can_place_task(Timeline* timeline, Task* task, int start_slot) {
    /* Check bounds */
    if (start_slot < 0 || start_slot + task->duration_slots > timeline->num_slots) {
        return false;
    }
    
    /* Check deadline constraint */
    if (task->deadline_slot >= 0) {
        int end_slot = start_slot + task->duration_slots;
        if (end_slot > task->deadline_slot) {
            return false;
        }
    }
    
    /* Check all required slots are available */
    for (int i = 0; i < task->duration_slots; i++) {
        if (!is_slot_available(timeline, start_slot + i)) {
            return false;
        }
    }
    
    return true;
}

/**
 * Place a task in the timeline at given slot
 */
static void place_task(Timeline* timeline, Task* task, int start_slot) {
    for (int i = 0; i < task->duration_slots; i++) {
        timeline->slots[start_slot + i].task_id = task->id;
    }
}

/**
 * Remove a task from the timeline
 */
static void remove_task(Timeline* timeline, Task* task, int start_slot) {
    for (int i = 0; i < task->duration_slots; i++) {
        timeline->slots[start_slot + i].task_id = -1;
    }
}

/**
 * Calculate energy match score for placing task at slot
 * Higher score = better match
 */
static int calculate_energy_score(Task* task, int slot_index) {
    int score = 0;
    
    /* Study and deep_work prefer peak energy */
    if (task->type == TASK_STUDY || task->type == TASK_DEEP_WORK) {
        if (is_peak_energy_period(slot_index)) {
            score += 10;
        } else if (is_medium_energy_period(slot_index)) {
            score += 5;
        }
    }
    /* Practice and revision accept medium energy */
    else if (task->type == TASK_PRACTICE || task->type == TASK_REVISION) {
        if (is_peak_energy_period(slot_index)) {
            score += 7;
        } else if (is_medium_energy_period(slot_index)) {
            score += 8; /* Slightly prefer medium for these */
        }
    }
    /* Breaks and free time prefer low energy */
    else if (task->type == TASK_BREAK || task->type == TASK_FREE_TIME) {
        if (is_low_energy_period(slot_index)) {
            score += 10;
        }
    }
    
    /* Match preferred energy if specified */
    if (task->preferred_energy != ENERGY_ANY) {
        if (task->preferred_energy == ENERGY_PREFER_PEAK && is_peak_energy_period(slot_index)) {
            score += 5;
        } else if (task->preferred_energy == ENERGY_PREFER_MEDIUM && is_medium_energy_period(slot_index)) {
            score += 5;
        } else if (task->preferred_energy == ENERGY_PREFER_LOW && is_low_energy_period(slot_index)) {
            score += 5;
        }
    }
    
    return score;
}


/* ============================================================
 * Backtracking Algorithm
 * Requirements: 2.1, 2.2, 2.3, 2.4
 * ============================================================ */

/**
 * Find best slot for a task based on energy matching
 * Returns -1 if no valid slot found
 * 
 * Note: This function is available for future use in greedy scheduling
 * approaches. Currently the backtracking algorithm handles slot selection
 * internally with energy scoring.
 */
#ifdef USE_GREEDY_SCHEDULER
static int find_best_slot(Timeline* timeline, Task* task) {
    int best_slot = -1;
    int best_score = -1;
    
    for (int slot = 0; slot < timeline->num_slots; slot++) {
        if (can_place_task(timeline, task, slot)) {
            int score = calculate_energy_score(task, slot);
            if (score > best_score) {
                best_score = score;
                best_slot = slot;
            }
        }
    }
    
    return best_slot;
}
#endif

/**
 * Recursive backtracking solver
 * @param timeline Current timeline state
 * @param tasks Array of tasks
 * @param num_tasks Total number of tasks
 * @param task_index Current task being placed
 * @param placements Array storing where each task is placed (-1 if not placed)
 * @return true if solution found
 */
static bool backtrack(
    Timeline* timeline,
    Task* tasks,
    int num_tasks,
    int task_index,
    int* placements
) {
    /* Base case: all tasks placed */
    if (task_index >= num_tasks) {
        return true;
    }
    
    Task* task = &tasks[task_index];
    
    /* Skip fixed tasks - they're already placed */
    if (task->is_fixed) {
        return backtrack(timeline, tasks, num_tasks, task_index + 1, placements);
    }
    
    /* Try each possible slot, prioritizing by energy score */
    /* First pass: collect all valid slots with scores */
    typedef struct {
        int slot;
        int score;
    } SlotScore;
    
    SlotScore candidates[MAX_SLOTS];
    int num_candidates = 0;
    
    for (int slot = 0; slot < timeline->num_slots; slot++) {
        if (can_place_task(timeline, task, slot)) {
            candidates[num_candidates].slot = slot;
            candidates[num_candidates].score = calculate_energy_score(task, slot);
            num_candidates++;
        }
    }
    
    /* Sort candidates by score (descending) - simple bubble sort for small arrays */
    for (int i = 0; i < num_candidates - 1; i++) {
        for (int j = 0; j < num_candidates - i - 1; j++) {
            if (candidates[j].score < candidates[j + 1].score) {
                SlotScore temp = candidates[j];
                candidates[j] = candidates[j + 1];
                candidates[j + 1] = temp;
            }
        }
    }
    
    /* Try each candidate slot */
    for (int i = 0; i < num_candidates; i++) {
        int slot = candidates[i].slot;
        
        /* Place task */
        place_task(timeline, task, slot);
        placements[task_index] = slot;
        
        /* Recurse */
        if (backtrack(timeline, tasks, num_tasks, task_index + 1, placements)) {
            return true;
        }
        
        /* Backtrack */
        remove_task(timeline, task, slot);
        placements[task_index] = -1;
    }
    
    return false;
}


/* ============================================================
 * Main Optimization Function
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
 * ============================================================ */

Timeline* optimize_schedule(
    Task* tasks,
    int num_tasks,
    TimeSlot* fixed_slots,
    int num_fixed
) {
    /* Validate inputs */
    if (num_tasks < 0 || num_tasks > MAX_TASKS) {
        Timeline* timeline = timeline_create();
        if (timeline) {
            timeline->success = false;
            snprintf(timeline->error_message, MAX_ERROR_LEN, 
                     "Invalid number of tasks: %d", num_tasks);
        }
        return timeline;
    }
    
    /* Create timeline (default 7 days) */
    Timeline* timeline = timeline_create();
    if (timeline == NULL) {
        return NULL;
    }
    
    /* Apply fixed slots first */
    if (fixed_slots != NULL && num_fixed > 0) {
        for (int i = 0; i < num_fixed; i++) {
            int idx = fixed_slots[i].slot_index;
            if (idx >= 0 && idx < timeline->num_slots) {
                timeline->slots[idx].task_id = fixed_slots[i].task_id;
                timeline->slots[idx].is_fixed = true;
            }
        }
    }
    
    /* Handle empty task list */
    if (tasks == NULL || num_tasks == 0) {
        timeline->success = true;
        return timeline;
    }
    
    /* Create working copy of tasks for sorting */
    Task* sorted_tasks = task_array_create(num_tasks);
    if (sorted_tasks == NULL) {
        timeline->success = false;
        snprintf(timeline->error_message, MAX_ERROR_LEN, 
                 "Memory allocation failed");
        return timeline;
    }
    memcpy(sorted_tasks, tasks, sizeof(Task) * num_tasks);
    
    /* Sort tasks by priority (highest first) */
    qsort(sorted_tasks, num_tasks, sizeof(Task), task_compare_priority);
    
    /* Initialize placements array */
    int* placements = (int*)malloc(sizeof(int) * num_tasks);
    if (placements == NULL) {
        task_array_free(sorted_tasks);
        timeline->success = false;
        snprintf(timeline->error_message, MAX_ERROR_LEN, 
                 "Memory allocation failed");
        return timeline;
    }
    for (int i = 0; i < num_tasks; i++) {
        placements[i] = -1;
    }
    
    /* Run backtracking algorithm */
    bool found = backtrack(timeline, sorted_tasks, num_tasks, 0, placements);
    
    if (found) {
        timeline->success = true;
    } else {
        timeline->success = false;
        snprintf(timeline->error_message, MAX_ERROR_LEN, 
                 "NO_SOLUTION: Cannot find valid placement for all tasks");
    }
    
    /* Cleanup */
    free(placements);
    task_array_free(sorted_tasks);
    
    return timeline;
}
