/**
 * AESA Core Scheduling Engine - JSON Output Implementation
 * 
 * Requirements: 2.6
 */

#include "json_output.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>

/* Initial buffer size for JSON output */
#define INITIAL_BUFFER_SIZE 4096
#define BUFFER_GROW_FACTOR 2

/* ============================================================
 * JSON String Escaping
 * ============================================================ */

/**
 * Escape a string for JSON output
 * Returns newly allocated string, caller must free
 */
static char* json_escape_string(const char* str) {
    if (str == NULL) {
        char* empty = (char*)malloc(3);
        if (empty) strcpy(empty, "\"\"");
        return empty;
    }
    
    /* Calculate required size */
    size_t len = strlen(str);
    size_t escaped_len = 2; /* For quotes */
    
    for (size_t i = 0; i < len; i++) {
        switch (str[i]) {
            case '"':
            case '\\':
            case '\b':
            case '\f':
            case '\n':
            case '\r':
            case '\t':
                escaped_len += 2;
                break;
            default:
                if ((unsigned char)str[i] < 32) {
                    escaped_len += 6; /* \uXXXX */
                } else {
                    escaped_len += 1;
                }
        }
    }
    
    char* result = (char*)malloc(escaped_len + 1);
    if (result == NULL) return NULL;
    
    char* p = result;
    *p++ = '"';
    
    for (size_t i = 0; i < len; i++) {
        switch (str[i]) {
            case '"':  *p++ = '\\'; *p++ = '"';  break;
            case '\\': *p++ = '\\'; *p++ = '\\'; break;
            case '\b': *p++ = '\\'; *p++ = 'b';  break;
            case '\f': *p++ = '\\'; *p++ = 'f';  break;
            case '\n': *p++ = '\\'; *p++ = 'n';  break;
            case '\r': *p++ = '\\'; *p++ = 'r';  break;
            case '\t': *p++ = '\\'; *p++ = 't';  break;
            default:
                if ((unsigned char)str[i] < 32) {
                    sprintf(p, "\\u%04x", (unsigned char)str[i]);
                    p += 6;
                } else {
                    *p++ = str[i];
                }
        }
    }
    
    *p++ = '"';
    *p = '\0';
    
    return result;
}


/* ============================================================
 * Dynamic String Buffer
 * ============================================================ */

typedef struct {
    char* data;
    size_t size;
    size_t capacity;
} StringBuffer;

static StringBuffer* buffer_create(void) {
    StringBuffer* buf = (StringBuffer*)malloc(sizeof(StringBuffer));
    if (buf == NULL) return NULL;
    
    buf->data = (char*)malloc(INITIAL_BUFFER_SIZE);
    if (buf->data == NULL) {
        free(buf);
        return NULL;
    }
    
    buf->data[0] = '\0';
    buf->size = 0;
    buf->capacity = INITIAL_BUFFER_SIZE;
    
    return buf;
}

static void buffer_free(StringBuffer* buf) {
    if (buf != NULL) {
        if (buf->data != NULL) {
            free(buf->data);
        }
        free(buf);
    }
}

static int buffer_append(StringBuffer* buf, const char* str) {
    if (buf == NULL || str == NULL) return -1;
    
    size_t len = strlen(str);
    size_t required = buf->size + len + 1;
    
    /* Grow buffer if needed */
    if (required > buf->capacity) {
        size_t new_capacity = buf->capacity * BUFFER_GROW_FACTOR;
        while (new_capacity < required) {
            new_capacity *= BUFFER_GROW_FACTOR;
        }
        
        char* new_data = (char*)realloc(buf->data, new_capacity);
        if (new_data == NULL) return -1;
        
        buf->data = new_data;
        buf->capacity = new_capacity;
    }
    
    strcpy(buf->data + buf->size, str);
    buf->size += len;
    
    return 0;
}

static int buffer_append_int(StringBuffer* buf, int value) {
    char temp[32];
    snprintf(temp, sizeof(temp), "%d", value);
    return buffer_append(buf, temp);
}

static char* buffer_detach(StringBuffer* buf) {
    if (buf == NULL) return NULL;
    char* result = buf->data;
    buf->data = NULL;
    buffer_free(buf);
    return result;
}


/* ============================================================
 * JSON Serialization
 * ============================================================ */

char* timeline_to_json(Timeline* timeline) {
    if (timeline == NULL) {
        return NULL;
    }
    
    StringBuffer* buf = buffer_create();
    if (buf == NULL) return NULL;
    
    buffer_append(buf, "{\n");
    
    /* Success field */
    buffer_append(buf, "  \"success\": ");
    buffer_append(buf, timeline->success ? "true" : "false");
    buffer_append(buf, ",\n");
    
    /* Error message (if any) */
    buffer_append(buf, "  \"error_message\": ");
    char* escaped_error = json_escape_string(timeline->error_message);
    if (escaped_error) {
        buffer_append(buf, escaped_error);
        free(escaped_error);
    } else {
        buffer_append(buf, "\"\"");
    }
    buffer_append(buf, ",\n");
    
    /* Number of slots */
    buffer_append(buf, "  \"num_slots\": ");
    buffer_append_int(buf, timeline->num_slots);
    buffer_append(buf, ",\n");
    
    /* Slots array */
    buffer_append(buf, "  \"slots\": [\n");
    
    for (int i = 0; i < timeline->num_slots; i++) {
        TimeSlot* slot = &timeline->slots[i];
        
        buffer_append(buf, "    {\n");
        
        buffer_append(buf, "      \"slot_index\": ");
        buffer_append_int(buf, slot->slot_index);
        buffer_append(buf, ",\n");
        
        buffer_append(buf, "      \"task_id\": ");
        buffer_append_int(buf, slot->task_id);
        buffer_append(buf, ",\n");
        
        buffer_append(buf, "      \"energy_level\": ");
        buffer_append_int(buf, slot->energy_level);
        buffer_append(buf, ",\n");
        
        buffer_append(buf, "      \"is_fixed\": ");
        buffer_append(buf, slot->is_fixed ? "true" : "false");
        buffer_append(buf, "\n");
        
        buffer_append(buf, "    }");
        
        if (i < timeline->num_slots - 1) {
            buffer_append(buf, ",");
        }
        buffer_append(buf, "\n");
    }
    
    buffer_append(buf, "  ]\n");
    buffer_append(buf, "}\n");
    
    return buffer_detach(buf);
}

void free_json(char* json) {
    if (json != NULL) {
        free(json);
    }
}


/* ============================================================
 * JSON Parsing Helpers
 * ============================================================ */

/**
 * Skip whitespace in JSON string
 */
static const char* skip_whitespace(const char* p) {
    while (*p && isspace((unsigned char)*p)) p++;
    return p;
}

/**
 * Parse a JSON integer
 */
static const char* parse_int(const char* p, int* value) {
    p = skip_whitespace(p);
    int sign = 1;
    if (*p == '-') {
        sign = -1;
        p++;
    }
    *value = 0;
    while (*p >= '0' && *p <= '9') {
        *value = *value * 10 + (*p - '0');
        p++;
    }
    *value *= sign;
    return p;
}

/**
 * Parse a JSON string (returns allocated string)
 */
static const char* parse_string(const char* p, char* dest, size_t max_len) {
    p = skip_whitespace(p);
    if (*p != '"') return NULL;
    p++;
    
    size_t i = 0;
    while (*p && *p != '"' && i < max_len - 1) {
        if (*p == '\\') {
            p++;
            switch (*p) {
                case '"':  dest[i++] = '"';  break;
                case '\\': dest[i++] = '\\'; break;
                case 'b':  dest[i++] = '\b'; break;
                case 'f':  dest[i++] = '\f'; break;
                case 'n':  dest[i++] = '\n'; break;
                case 'r':  dest[i++] = '\r'; break;
                case 't':  dest[i++] = '\t'; break;
                default:   dest[i++] = *p;   break;
            }
        } else {
            dest[i++] = *p;
        }
        p++;
    }
    dest[i] = '\0';
    
    if (*p == '"') p++;
    return p;
}

/**
 * Parse a JSON boolean
 */
static const char* parse_bool(const char* p, bool* value) {
    p = skip_whitespace(p);
    if (strncmp(p, "true", 4) == 0) {
        *value = true;
        return p + 4;
    } else if (strncmp(p, "false", 5) == 0) {
        *value = false;
        return p + 5;
    }
    return NULL;
}

/**
 * Find a key in JSON object
 */
static const char* find_key(const char* p, const char* key) {
    char search[256];
    snprintf(search, sizeof(search), "\"%s\"", key);
    
    const char* found = strstr(p, search);
    if (found == NULL) return NULL;
    
    found += strlen(search);
    found = skip_whitespace(found);
    if (*found == ':') found++;
    return skip_whitespace(found);
}


/* ============================================================
 * JSON Input Parsing
 * ============================================================ */

/**
 * Count array elements in JSON
 */
static int count_array_elements(const char* p) {
    if (*p != '[') return 0;
    const char* start = p;
    p++;
    
    int count = 0;
    int depth = 0;
    bool in_string = false;
    
    while (*p) {
        if (*p == '"' && (p == start || *(p-1) != '\\')) {
            in_string = !in_string;
        } else if (!in_string) {
            if (*p == '{') {
                if (depth == 0) count++;
                depth++;
            } else if (*p == '}') {
                depth--;
            } else if (*p == ']' && depth == 0) {
                break;
            }
        }
        p++;
    }
    
    return count;
}

int parse_json_input(
    const char* json_input,
    Task** tasks,
    int* num_tasks,
    TimeSlot** fixed_slots,
    int* num_fixed
) {
    if (json_input == NULL || tasks == NULL || num_tasks == NULL ||
        fixed_slots == NULL || num_fixed == NULL) {
        return -1;
    }
    
    *tasks = NULL;
    *num_tasks = 0;
    *fixed_slots = NULL;
    *num_fixed = 0;
    
    /* Find tasks array */
    const char* tasks_start = find_key(json_input, "tasks");
    if (tasks_start && *tasks_start == '[') {
        int count = count_array_elements(tasks_start);
        if (count > 0 && count <= MAX_TASKS) {
            *tasks = task_array_create(count);
            if (*tasks == NULL) return -1;
            *num_tasks = count;
            
            /* Parse each task */
            const char* p = tasks_start + 1;
            for (int i = 0; i < count; i++) {
                p = skip_whitespace(p);
                if (*p != '{') break;
                
                /* Find end of this object */
                const char* obj_start = p;
                int depth = 1;
                p++;
                while (*p && depth > 0) {
                    if (*p == '{') depth++;
                    else if (*p == '}') depth--;
                    p++;
                }
                
                /* Parse task fields */
                Task* task = &(*tasks)[i];
                const char* val;
                
                if ((val = find_key(obj_start, "id"))) {
                    parse_int(val, &task->id);
                }
                if ((val = find_key(obj_start, "name"))) {
                    parse_string(val, task->name, MAX_NAME_LEN);
                }
                if ((val = find_key(obj_start, "type"))) {
                    char type_str[64];
                    parse_string(val, type_str, sizeof(type_str));
                    int type = task_type_from_string(type_str);
                    if (type >= 0) task->type = (TaskType)type;
                }
                if ((val = find_key(obj_start, "duration_slots"))) {
                    parse_int(val, &task->duration_slots);
                }
                if ((val = find_key(obj_start, "priority"))) {
                    parse_int(val, &task->priority);
                }
                if ((val = find_key(obj_start, "deadline_slot"))) {
                    parse_int(val, &task->deadline_slot);
                }
                if ((val = find_key(obj_start, "is_fixed"))) {
                    parse_bool(val, &task->is_fixed);
                }
                if ((val = find_key(obj_start, "preferred_energy"))) {
                    int energy;
                    parse_int(val, &energy);
                    task->preferred_energy = (PreferredEnergy)energy;
                }
                
                /* Skip comma */
                p = skip_whitespace(p);
                if (*p == ',') p++;
            }
        }
    }
    
    /* Find fixed_slots array */
    const char* fixed_start = find_key(json_input, "fixed_slots");
    if (fixed_start && *fixed_start == '[') {
        int count = count_array_elements(fixed_start);
        if (count > 0 && count <= MAX_SLOTS) {
            *fixed_slots = timeslot_array_create(count);
            if (*fixed_slots == NULL) {
                task_array_free(*tasks);
                *tasks = NULL;
                *num_tasks = 0;
                return -1;
            }
            *num_fixed = count;
            
            /* Parse each fixed slot */
            const char* p = fixed_start + 1;
            for (int i = 0; i < count; i++) {
                p = skip_whitespace(p);
                if (*p != '{') break;
                
                const char* obj_start = p;
                int depth = 1;
                p++;
                while (*p && depth > 0) {
                    if (*p == '{') depth++;
                    else if (*p == '}') depth--;
                    p++;
                }
                
                TimeSlot* slot = &(*fixed_slots)[i];
                const char* val;
                
                if ((val = find_key(obj_start, "slot_index"))) {
                    parse_int(val, &slot->slot_index);
                }
                if ((val = find_key(obj_start, "task_id"))) {
                    parse_int(val, &slot->task_id);
                }
                slot->is_fixed = true;
                
                p = skip_whitespace(p);
                if (*p == ',') p++;
            }
        }
    }
    
    return 0;
}
