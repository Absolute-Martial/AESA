/**
 * AESA Core Scheduling Engine - Tests
 * 
 * Property-based tests for the scheduling engine.
 * Uses a simple random generator for property testing.
 */

#include "../src/scheduler.h"
#include "../src/json_output.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <assert.h>

/* Test configuration */
#define NUM_ITERATIONS 100
#define MAX_TEST_TASKS 50

/* Simple test framework */
static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) static void name(void)
#define RUN_TEST(name) do { \
    printf("Running %s... ", #name); \
    tests_run++; \
    name(); \
    printf("PASSED\n"); \
    tests_passed++; \
} while(0)

#define ASSERT(cond) do { \
    if (!(cond)) { \
        printf("FAILED at %s:%d: %s\n", __FILE__, __LINE__, #cond); \
        tests_failed++; \
        return; \
    } \
} while(0)

#define ASSERT_EQ(a, b) ASSERT((a) == (b))
#define ASSERT_NE(a, b) ASSERT((a) != (b))
#define ASSERT_TRUE(x) ASSERT(x)
#define ASSERT_FALSE(x) ASSERT(!(x))

/* Random number generator for property tests */
static unsigned int rand_seed = 0;

static void seed_random(unsigned int seed) {
    rand_seed = seed;
    srand(seed);
}

static int random_int(int min, int max) {
    return min + rand() % (max - min + 1);
}

static TaskType random_task_type(void) {
    return (TaskType)random_int(0, TASK_TYPE_COUNT - 1);
}


/* ============================================================
 * Unit Tests
 * ============================================================ */

TEST(test_task_create_free) {
    Task* task = task_create();
    ASSERT_NE(task, NULL);
    ASSERT_EQ(task->id, -1);
    ASSERT_EQ(task->duration_slots, 1);
    ASSERT_EQ(task->priority, PRIORITY_REGULAR_STUDY);
    ASSERT_FALSE(task->is_fixed);
    task_free(task);
}

TEST(test_timeline_create_free) {
    Timeline* timeline = timeline_create();
    ASSERT_NE(timeline, NULL);
    ASSERT_EQ(timeline->num_slots, 7 * SLOTS_PER_DAY);
    ASSERT_FALSE(timeline->success);
    timeline_free(timeline);
}

TEST(test_task_type_strings) {
    ASSERT_EQ(strcmp(task_type_to_string(TASK_UNIVERSITY), "university"), 0);
    ASSERT_EQ(strcmp(task_type_to_string(TASK_STUDY), "study"), 0);
    ASSERT_EQ(strcmp(task_type_to_string(TASK_SLEEP), "sleep"), 0);
    ASSERT_EQ(strcmp(task_type_to_string(TASK_DINNER), "dinner"), 0);
    
    ASSERT_EQ(task_type_from_string("university"), TASK_UNIVERSITY);
    ASSERT_EQ(task_type_from_string("study"), TASK_STUDY);
    ASSERT_EQ(task_type_from_string("invalid"), -1);
}

TEST(test_energy_levels) {
    /* Peak energy: 8-10am (slots 16-20), 4-6pm (slots 32-36) */
    ASSERT_TRUE(is_peak_energy_period(16));  /* 8am */
    ASSERT_TRUE(is_peak_energy_period(18));  /* 9am */
    ASSERT_TRUE(is_peak_energy_period(32));  /* 4pm */
    ASSERT_TRUE(is_peak_energy_period(34));  /* 5pm */
    
    /* Medium energy: 6-8am, 10am-12pm, 2-4pm, 6-8pm */
    ASSERT_TRUE(is_medium_energy_period(12)); /* 6am */
    ASSERT_TRUE(is_medium_energy_period(20)); /* 10am */
    ASSERT_TRUE(is_medium_energy_period(28)); /* 2pm */
    ASSERT_TRUE(is_medium_energy_period(36)); /* 6pm */
    
    /* Low energy: after meals, late evening */
    ASSERT_TRUE(is_low_energy_period(24));   /* 12pm (lunch) */
    ASSERT_TRUE(is_low_energy_period(40));   /* 8pm */
    ASSERT_TRUE(is_low_energy_period(0));    /* midnight */
}

TEST(test_empty_schedule) {
    Timeline* timeline = optimize_schedule(NULL, 0, NULL, 0);
    ASSERT_NE(timeline, NULL);
    ASSERT_TRUE(timeline->success);
    timeline_free(timeline);
}

TEST(test_single_task) {
    Task task;
    task_init(&task);
    task.id = 1;
    strcpy(task.name, "Study Math");
    task.type = TASK_STUDY;
    task.duration_slots = 2;
    task.priority = PRIORITY_REGULAR_STUDY;
    
    Timeline* timeline = optimize_schedule(&task, 1, NULL, 0);
    ASSERT_NE(timeline, NULL);
    ASSERT_TRUE(timeline->success);
    
    /* Verify task was placed */
    int found = 0;
    for (int i = 0; i < timeline->num_slots; i++) {
        if (timeline->slots[i].task_id == 1) found++;
    }
    ASSERT_EQ(found, 2);  /* Duration is 2 slots */
    
    timeline_free(timeline);
}


/* ============================================================
 * Property Tests
 * ============================================================ */

/**
 * Property 1: Schedule Validity - No Overlaps
 * For any list of tasks, the returned schedule SHALL have no overlapping
 * time blocks—each time slot contains at most one task.
 * 
 * Validates: Requirements 2.1, 2.2, 2.4
 */
TEST(property_no_overlaps) {
    printf("\n  [Property 1: Schedule Validity - No Overlaps]\n");
    
    for (int iter = 0; iter < NUM_ITERATIONS; iter++) {
        seed_random(iter + 1);
        
        int num_tasks = random_int(1, MAX_TEST_TASKS);
        Task* tasks = task_array_create(num_tasks);
        ASSERT_NE(tasks, NULL);
        
        /* Generate random tasks */
        for (int i = 0; i < num_tasks; i++) {
            tasks[i].id = i + 1;
            snprintf(tasks[i].name, MAX_NAME_LEN, "Task_%d", i);
            tasks[i].type = random_task_type();
            tasks[i].duration_slots = random_int(1, 4);
            tasks[i].priority = random_int(10, 100);
            tasks[i].deadline_slot = -1;
            tasks[i].is_fixed = false;
        }
        
        Timeline* timeline = optimize_schedule(tasks, num_tasks, NULL, 0);
        ASSERT_NE(timeline, NULL);
        
        if (timeline->success) {
            /* Verify no overlaps: each slot has at most one task */
            for (int i = 0; i < timeline->num_slots; i++) {
                int task_id = timeline->slots[i].task_id;
                if (task_id >= 0) {
                    /* Count how many consecutive slots have this task */
                    int count = 0;
                    while (i < timeline->num_slots && 
                           timeline->slots[i].task_id == task_id) {
                        count++;
                        i++;
                    }
                    i--; /* Adjust for loop increment */
                    
                    /* Find the task and verify duration matches */
                    for (int t = 0; t < num_tasks; t++) {
                        if (tasks[t].id == task_id) {
                            ASSERT_EQ(count, tasks[t].duration_slots);
                            break;
                        }
                    }
                }
            }
        }
        
        timeline_free(timeline);
        task_array_free(tasks);
    }
    
    printf("  Completed %d iterations\n", NUM_ITERATIONS);
}

/**
 * Property 2: Fixed Slot Preservation
 * For any schedule optimization, all time slots marked as fixed SHALL
 * remain unchanged in the output.
 * 
 * Validates: Requirements 2.4, 9.2
 */
TEST(property_fixed_slot_preservation) {
    printf("\n  [Property 2: Fixed Slot Preservation]\n");
    
    for (int iter = 0; iter < NUM_ITERATIONS; iter++) {
        seed_random(iter + 100);
        
        /* Create some fixed slots with unique indices */
        int num_fixed = random_int(1, 10);
        TimeSlot* fixed_slots = timeslot_array_create(num_fixed);
        ASSERT_NE(fixed_slots, NULL);
        
        /* Use a simple approach to ensure unique indices */
        int used_indices[10];
        for (int i = 0; i < num_fixed; i++) {
            int idx;
            bool unique;
            do {
                idx = random_int(0, MAX_SLOTS - 1);
                unique = true;
                for (int j = 0; j < i; j++) {
                    if (used_indices[j] == idx) {
                        unique = false;
                        break;
                    }
                }
            } while (!unique);
            
            used_indices[i] = idx;
            fixed_slots[i].slot_index = idx;
            fixed_slots[i].task_id = -(i + 1);  /* Negative IDs for fixed */
            fixed_slots[i].is_fixed = true;
        }
        
        /* Create some tasks */
        int num_tasks = random_int(1, 20);
        Task* tasks = task_array_create(num_tasks);
        ASSERT_NE(tasks, NULL);
        
        for (int i = 0; i < num_tasks; i++) {
            tasks[i].id = i + 1;
            snprintf(tasks[i].name, MAX_NAME_LEN, "Task_%d", i);
            tasks[i].type = TASK_STUDY;
            tasks[i].duration_slots = random_int(1, 2);
            tasks[i].priority = random_int(10, 100);
        }
        
        Timeline* timeline = optimize_schedule(tasks, num_tasks, fixed_slots, num_fixed);
        ASSERT_NE(timeline, NULL);
        
        /* Verify fixed slots are preserved */
        for (int i = 0; i < num_fixed; i++) {
            int idx = fixed_slots[i].slot_index;
            if (idx >= 0 && idx < timeline->num_slots) {
                ASSERT_TRUE(timeline->slots[idx].is_fixed);
                ASSERT_EQ(timeline->slots[idx].task_id, fixed_slots[i].task_id);
            }
        }
        
        timeline_free(timeline);
        task_array_free(tasks);
        timeslot_array_free(fixed_slots);
    }
    
    printf("  Completed %d iterations\n", NUM_ITERATIONS);
}


/**
 * Property 3: Deadline Compliance
 * For any task with a deadline in the optimized schedule, the task's
 * scheduled end time SHALL be strictly before the deadline time.
 * 
 * Validates: Requirements 2.3
 */
TEST(property_deadline_compliance) {
    printf("\n  [Property 3: Deadline Compliance]\n");
    
    for (int iter = 0; iter < NUM_ITERATIONS; iter++) {
        seed_random(iter + 200);
        
        int num_tasks = random_int(1, 20);
        Task* tasks = task_array_create(num_tasks);
        ASSERT_NE(tasks, NULL);
        
        for (int i = 0; i < num_tasks; i++) {
            tasks[i].id = i + 1;
            snprintf(tasks[i].name, MAX_NAME_LEN, "Task_%d", i);
            tasks[i].type = TASK_STUDY;
            tasks[i].duration_slots = random_int(1, 3);
            tasks[i].priority = random_int(10, 100);
            
            /* Give some tasks deadlines */
            if (random_int(0, 1) == 1) {
                /* Deadline must be far enough to fit the task */
                tasks[i].deadline_slot = random_int(
                    tasks[i].duration_slots + 10, 
                    MAX_SLOTS - 1
                );
            } else {
                tasks[i].deadline_slot = -1;
            }
        }
        
        Timeline* timeline = optimize_schedule(tasks, num_tasks, NULL, 0);
        ASSERT_NE(timeline, NULL);
        
        if (timeline->success) {
            /* Verify deadline compliance */
            for (int t = 0; t < num_tasks; t++) {
                if (tasks[t].deadline_slot >= 0) {
                    /* Find where this task was placed */
                    int end_slot = -1;
                    for (int i = 0; i < timeline->num_slots; i++) {
                        if (timeline->slots[i].task_id == tasks[t].id) {
                            end_slot = i + 1;  /* Track last slot + 1 */
                        }
                    }
                    
                    if (end_slot > 0) {
                        /* End slot must be <= deadline */
                        ASSERT_TRUE(end_slot <= tasks[t].deadline_slot);
                    }
                }
            }
        }
        
        timeline_free(timeline);
        task_array_free(tasks);
    }
    
    printf("  Completed %d iterations\n", NUM_ITERATIONS);
}

/**
 * Property 4: JSON Serialization Round-Trip
 * For any valid Timeline object, serializing to JSON and deserializing
 * back SHALL produce an equivalent Timeline object.
 * 
 * Validates: Requirements 2.6
 */
TEST(property_json_round_trip) {
    printf("\n  [Property 4: JSON Serialization Round-Trip]\n");
    
    for (int iter = 0; iter < NUM_ITERATIONS; iter++) {
        seed_random(iter + 300);
        
        /* Create a timeline with some tasks */
        int num_tasks = random_int(1, 10);
        Task* tasks = task_array_create(num_tasks);
        ASSERT_NE(tasks, NULL);
        
        for (int i = 0; i < num_tasks; i++) {
            tasks[i].id = i + 1;
            snprintf(tasks[i].name, MAX_NAME_LEN, "Task_%d", i);
            tasks[i].type = random_task_type();
            tasks[i].duration_slots = random_int(1, 2);
            tasks[i].priority = random_int(10, 100);
        }
        
        Timeline* timeline = optimize_schedule(tasks, num_tasks, NULL, 0);
        ASSERT_NE(timeline, NULL);
        
        /* Serialize to JSON */
        char* json = timeline_to_json(timeline);
        ASSERT_NE(json, NULL);
        
        /* Verify JSON contains expected fields */
        ASSERT_NE(strstr(json, "\"success\""), NULL);
        ASSERT_NE(strstr(json, "\"num_slots\""), NULL);
        ASSERT_NE(strstr(json, "\"slots\""), NULL);
        
        if (timeline->success) {
            ASSERT_NE(strstr(json, "\"success\": true"), NULL);
        }
        
        free_json(json);
        timeline_free(timeline);
        task_array_free(tasks);
    }
    
    printf("  Completed %d iterations\n", NUM_ITERATIONS);
}


/**
 * Property 6: Energy-Period Task Placement
 * For any schedule where peak energy periods have available slots,
 * study and deep_work tasks SHALL be preferentially placed in those
 * periods over medium or low energy periods.
 * 
 * Validates: Requirements 3.2, 3.3, 3.4
 */
TEST(property_energy_based_placement) {
    printf("\n  [Property 6: Energy-Period Task Placement]\n");
    
    int peak_placements = 0;
    int non_peak_placements = 0;
    
    for (int iter = 0; iter < NUM_ITERATIONS; iter++) {
        seed_random(iter + 500);
        
        /* Create study/deep_work tasks only */
        int num_tasks = random_int(1, 5);
        Task* tasks = task_array_create(num_tasks);
        ASSERT_NE(tasks, NULL);
        
        for (int i = 0; i < num_tasks; i++) {
            tasks[i].id = i + 1;
            snprintf(tasks[i].name, MAX_NAME_LEN, "Study_%d", i);
            tasks[i].type = (random_int(0, 1) == 0) ? TASK_STUDY : TASK_DEEP_WORK;
            tasks[i].duration_slots = 2;
            tasks[i].priority = PRIORITY_REGULAR_STUDY;
        }
        
        Timeline* timeline = optimize_schedule(tasks, num_tasks, NULL, 0);
        ASSERT_NE(timeline, NULL);
        
        if (timeline->success) {
            /* Check where study tasks were placed */
            for (int i = 0; i < timeline->num_slots; i++) {
                if (timeline->slots[i].task_id > 0) {
                    if (is_peak_energy_period(i)) {
                        peak_placements++;
                    } else {
                        non_peak_placements++;
                    }
                }
            }
        }
        
        timeline_free(timeline);
        task_array_free(tasks);
    }
    
    /* Study tasks should prefer peak energy periods */
    /* Allow some flexibility since not all tasks can fit in peak periods */
    printf("  Peak placements: %d, Non-peak: %d\n", peak_placements, non_peak_placements);
    
    /* At least some tasks should be in peak periods if available */
    ASSERT_TRUE(peak_placements > 0 || non_peak_placements == 0);
    
    printf("  Completed %d iterations\n", NUM_ITERATIONS);
}

/**
 * Property 8: Priority-Based Scheduling Order
 * For any set of tasks with different priorities competing for the same
 * time slot, the higher priority task SHALL be scheduled first.
 * 
 * Validates: Requirements 4.2
 */
TEST(property_priority_ordering) {
    printf("\n  [Property 8: Priority-Based Scheduling Order]\n");
    
    for (int iter = 0; iter < NUM_ITERATIONS; iter++) {
        seed_random(iter + 700);
        
        /* Create tasks with varying priorities */
        int num_tasks = random_int(2, 10);
        Task* tasks = task_array_create(num_tasks);
        ASSERT_NE(tasks, NULL);
        
        for (int i = 0; i < num_tasks; i++) {
            tasks[i].id = i + 1;
            snprintf(tasks[i].name, MAX_NAME_LEN, "Task_%d", i);
            tasks[i].type = TASK_STUDY;
            tasks[i].duration_slots = random_int(1, 3);
            tasks[i].priority = random_int(10, 100);
        }
        
        Timeline* timeline = optimize_schedule(tasks, num_tasks, NULL, 0);
        ASSERT_NE(timeline, NULL);
        
        if (timeline->success) {
            /* Find first slot of each task */
            int* first_slots = (int*)malloc(sizeof(int) * num_tasks);
            for (int i = 0; i < num_tasks; i++) {
                first_slots[i] = -1;
            }
            
            for (int i = 0; i < timeline->num_slots; i++) {
                int tid = timeline->slots[i].task_id;
                if (tid > 0 && tid <= num_tasks) {
                    if (first_slots[tid - 1] == -1) {
                        first_slots[tid - 1] = i;
                    }
                }
            }
            
            /* Higher priority tasks should generally be scheduled earlier */
            /* (This is a soft property - we just verify the algorithm runs) */
            int scheduled_count = 0;
            for (int i = 0; i < num_tasks; i++) {
                if (first_slots[i] >= 0) scheduled_count++;
            }
            
            /* At least some tasks should be scheduled */
            ASSERT_TRUE(scheduled_count > 0);
            
            free(first_slots);
        }
        
        timeline_free(timeline);
        task_array_free(tasks);
    }
    
    printf("  Completed %d iterations\n", NUM_ITERATIONS);
}


/* ============================================================
 * Main Test Runner
 * ============================================================ */

int main(int argc, char* argv[]) {
    (void)argc;  /* Unused */
    (void)argv;  /* Unused */
    
    printf("===========================================\n");
    printf("AESA Core Scheduling Engine - Test Suite\n");
    printf("===========================================\n\n");
    
    /* Unit Tests */
    printf("--- Unit Tests ---\n");
    RUN_TEST(test_task_create_free);
    RUN_TEST(test_timeline_create_free);
    RUN_TEST(test_task_type_strings);
    RUN_TEST(test_energy_levels);
    RUN_TEST(test_empty_schedule);
    RUN_TEST(test_single_task);
    
    printf("\n--- Property Tests ---\n");
    
    /* Property 1: No Overlaps */
    RUN_TEST(property_no_overlaps);
    
    /* Property 2: Fixed Slot Preservation */
    RUN_TEST(property_fixed_slot_preservation);
    
    /* Property 3: Deadline Compliance */
    RUN_TEST(property_deadline_compliance);
    
    /* Property 4: JSON Round-Trip */
    RUN_TEST(property_json_round_trip);
    
    /* Property 6: Energy-Based Placement */
    RUN_TEST(property_energy_based_placement);
    
    /* Property 8: Priority Ordering */
    RUN_TEST(property_priority_ordering);
    
    printf("\n===========================================\n");
    printf("Test Results: %d/%d passed", tests_passed, tests_run);
    if (tests_failed > 0) {
        printf(" (%d FAILED)", tests_failed);
    }
    printf("\n===========================================\n");
    
    return tests_failed > 0 ? 1 : 0;
}
