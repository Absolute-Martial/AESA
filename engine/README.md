# AESA Core Scheduling Engine

C-based constraint satisfaction solver for optimal task scheduling.

## Overview

This engine implements a backtracking algorithm with energy-based heuristics to schedule tasks into optimal time slots. It's designed to be called from the Python backend via subprocess with JSON input/output.

## Features

- **Backtracking CSP Solver**: Finds valid task placements respecting all constraints
- **Energy-Based Scheduling**: Prioritizes high-energy periods for demanding tasks
- **Priority Ordering**: Schedules higher priority tasks first
- **Deadline Compliance**: Ensures tasks complete before their deadlines
- **Fixed Slot Preservation**: Respects immutable time blocks (classes, sleep)

## Building

```bash
# Build release version
make

# Build debug version
make debug

# Run tests
make test

# Memory check (requires valgrind)
make memcheck

# Clean build artifacts
make clean
```

## Usage

The scheduler reads JSON from stdin and outputs JSON to stdout:

```bash
./scheduler < input.json > output.json
```

### Input Format

```json
{
  "tasks": [
    {
      "id": 1,
      "name": "Study Math",
      "type": "study",
      "duration_slots": 2,
      "priority": 50,
      "deadline_slot": -1,
      "is_fixed": false,
      "preferred_energy": 3
    }
  ],
  "fixed_slots": [
    {
      "slot_index": 18,
      "task_id": -1
    }
  ],
  "num_days": 7
}
```

### Output Format

```json
{
  "success": true,
  "error_message": "",
  "num_slots": 336,
  "slots": [
    {
      "slot_index": 0,
      "task_id": -1,
      "energy_level": 3,
      "is_fixed": false
    }
  ]
}
```

## Task Types

| Type | Description |
|------|-------------|
| university | University classes |
| study | Study sessions |
| revision | Revision/review |
| practice | Practice problems |
| assignment | Assignments |
| lab_work | Lab work |
| deep_work | Deep work sessions |
| break | Breaks |
| free_time | Free time |
| sleep | Sleep |
| wake_routine | Morning routine |
| breakfast | Breakfast |
| lunch | Lunch |
| dinner | Dinner |

## Energy Periods

- **Peak (8-10)**: 8-10am, 4-6pm - Best for study/deep_work
- **Medium (5-7)**: 6-8am, 10am-12pm, 2-4pm, 6-8pm - Good for practice/revision
- **Low (3-5)**: After meals, late evening - Best for breaks/free_time

## Requirements

- GCC with C99 support
- Make
- Valgrind (optional, for memory checking)

## License

Part of the AESA project.
