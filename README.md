# PawPal+ — Pet Care Scheduling Assistant

PawPal+ is a Streamlit web application that helps pet owners plan, schedule, and track daily care tasks for one or more pets. It generates a chronological daily schedule, warns about conflicts, auto-advances recurring tasks, and surfaces priority-based recommendations.

---

## Screenshots

**Owner & Pet registration form**
![Owner & Pet form](live_pic%20(1).png)

**Add a Task — Feeding task with priority slider**
![Add a Task form](live_pic%20(4).png)

**Today's Schedule — task details card with "Mark done" button**
![Today's Schedule with task card](live_pic%20(3).png)

**Schedule summary — conflict check, metrics, and status indicators**
![Schedule summary and metrics](live_pic%20(2).png)

---

## Table of Contents

1. [Features](#features)
2. [Getting Started](#getting-started)
3. [Usage Guide](#usage-guide)
4. [Architecture Overview](#architecture-overview)
5. [Testing](#testing)
6. [Confidence & Known Gaps](#confidence--known-gaps)

---

## Features

### 1. Chronological Schedule (Time-Sorted Display)
Tasks are always displayed earliest-first regardless of insertion order.
`Scheduler.sort_by_time()` runs Python's built-in **Timsort** (`O(n log n)`) on the task list using `due_time` as the sort key. `Scheduler.add_task()` also re-sorts the master list on every insert, so the schedule stays ordered in real time.

### 2. Flexible Task Filtering
`PetCareSystem.filter_tasks(status, pet_name)` lets you query tasks by:
- **Completion status** — `pending`, `complete`, or `in_progress`
- **Pet name** — case-insensitive substring match
- **Both combined** — applied sequentially using list comprehensions

An unrecognised status raises a `ValueError` (validated against a `set` for O(1) membership check). An unknown pet name returns `[]` instead of raising.
Results are passed through `sort_by_time()` so filtered output is always chronological.

### 3. Conflict Detection
Two levels of conflict detection catch scheduling clashes before they cause problems:

| Method | Scope | Algorithm |
|---|---|---|
| `Scheduler.detect_conflicts(pet_id, window_minutes)` | Single pet | O(n²) pairwise comparison of non-complete tasks; flags pairs whose `due_time` gap ≤ `window_minutes` |
| `Scheduler.detect_all_conflicts(window_minutes)` | All pets | Same O(n²) loop across the full task list — catches both same-pet and cross-pet overlaps |

`PetCareSystem.get_conflict_warnings()` formats raw `(Task, Task)` pairs into human-readable strings labelled `[same-pet]` or `[cross-pet]`, using a `{pet_id: pet_name}` dict for O(1) name lookup. The Streamlit UI shows these warnings automatically whenever a schedule is displayed.

### 4. Automatic Daily & Weekly Recurrence
When a recurring task is completed, `Scheduler.generate_next_occurrence()` clones it and schedules the follow-up automatically:

- **Daily** — next occurrence is anchored to `today + 1 day`
- **Weekly** — next occurrence is anchored to `today + 7 days`
- **Monthly** — not auto-generated; managed manually to avoid month-end arithmetic edge cases

The clone preserves the original **time-of-day** (e.g. an 08:30 task stays at 08:30). Crucially, the next date is anchored to *today* rather than the original due time, so completing an overdue task never creates a near-immediate follow-up. `copy.copy()` is used to clone the task; per-occurrence state fields (`last_fed`, `last_dose_time`, `start_time`, `actual_duration`) are reset to `None` on the clone.

### 5. Priority-Based Task Suggestion
`Scheduler.prioritize_tasks()` scores every task using `Task.calculate_priority()`:
- Completed tasks → score `0`
- Overdue + pending → `priority + 10` (urgency boost)
- Normal pending → `priority` (1–10 slider set by the user)

Tasks are sorted descending by score. `Scheduler.suggest_next_task()` returns the single highest-priority pending task, surfaced in the UI as a recommendation.

### 6. Specialized Task Types
Four task subclasses extend the base `Task` with domain-specific tracking:

| Type | Extra Fields | Extra Behaviour |
|---|---|---|
| `FeedingTask` | food type, portion size, diet notes, last-fed timestamp | `record_feeding()` timestamps the meal and marks complete |
| `WalkTask` | duration goal, distance goal, location, start/end time | `start_walk()` sets status to `in_progress`; `end_walk()` computes elapsed minutes |
| `MedicationTask` | medication name, dosage, instructions, refill date | `check_refill_needed()` compares today against refill date; `validate_schedule()` flags medication time collisions |
| `AppointmentTask` | provider name, location, contact info, reminder time | `reschedule()` updates both due time and reminder; `add_provider_notes()` accumulates provider notes |

### 7. Medication Schedule Validation
`PetCareSystem.validate_pet_medication_schedule(pet_id)` checks each `MedicationTask` against all other medication tasks for the same pet. Any two medications sharing an exact `due_time` are flagged, returning a dict of `{medication_name: [conflicting_names]}`.

### 8. System Summary Metrics
`PetCareSystem.get_system_summary()` returns a snapshot dict with counts for total pets, total tasks, overdue tasks, upcoming tasks, and pending reminders. The Streamlit UI renders these as live metric tiles.

---

## Getting Started

### Requirements

- Python 3.9 or later
- pip

### Setup

```bash
# 1. Clone or download the project
# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

### Run the Web App

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` in your browser.

### Run the CLI Demo

```bash
python main.py
```

Prints a full schedule demo, conflict detection demo, and filtering demo using two pre-loaded pets (Buddy and Luna) with intentional conflicts.

---

## Usage Guide

### Step 1 — Add a Pet
Fill in the **Owner & Pet** section: owner name, pet name, species, breed, age, weight, and optional notes. Submit to register the pet. You can add multiple pets and switch between them with the active-pet selector.

### Step 2 — Add Tasks
Use the **Add a Task** section to create tasks for the active pet:
- Choose the task type (Feeding, Walk, Medication, Appointment)
- Set a title, description, due date, and due time
- Adjust the priority slider (1 = low, 10 = critical)
- Enable recurrence and choose Daily or Weekly if the task repeats
- Fill in type-specific fields (food type, medication name, provider, etc.)

### Step 3 — View & Manage the Schedule
Click **View Schedule** to generate today's plan. The schedule shows:
- A summary table (time, task, type, priority, recurrence, status)
- Detailed cards per task with a **Mark Done** button
- Overdue indicators (red circle) and refill warnings for medications
- Conflict warnings (`[same-pet]` or `[cross-pet]`) when tasks overlap within 30 minutes
- Summary metrics (pets, tasks, overdue, upcoming) at the bottom

Clicking **Mark Done** completes the task and, for daily/weekly recurring tasks, automatically schedules the next occurrence.

---

## Architecture Overview

```
PetCareSystem  (facade — the only entry point for UI/CLI)
├── _pets: list[Pet]
│   └── Pet._tasks: list[Task]       ← per-pet authoritative store
├── _scheduler: Scheduler
│   └── _tasks: list[Task]           ← same object references as Pet._tasks
└── _reminders: list[Reminder]
```

**Dual-ownership sync:** `PetCareSystem.add_task_to_pet()` is the single write path. It adds the task to both `Pet._tasks` and `Scheduler._tasks` using the same object reference — no data duplication, no drift.

**Key design patterns:**
- **Facade** — `PetCareSystem` shields callers from `Scheduler` and `Pet` internals
- **Inheritance** — `FeedingTask`, `WalkTask`, `MedicationTask`, `AppointmentTask` all extend `Task`
- **Delegation** — priority scoring logic lives on `Task.calculate_priority()`, not inside `Scheduler`
- **Today-anchored recurrence** — prevents cascading overdue follow-ups when tasks are completed late

---

## Testing

### Run the Test Suite

```bash
python -m pytest tests/test_pawpal.py -v
```

Or without pytest installed:

```bash
python tests/test_pawpal.py
```

### Test Coverage

| Category | Tests | What is verified |
|---|---|---|
| **Task basics** | `test_mark_complete_changes_status` | `mark_complete()` flips status to `complete` |
| | `test_add_task_increases_pet_task_count` | `Pet.add_task()` increases the pet's task count by exactly 1 |
| **Sorting** | `test_sort_by_time_returns_chronological_order` | Tasks added out of order come back earliest-first |
| | `test_sort_by_time_empty_list` | Sorting an empty scheduler returns `[]` without raising |
| | `test_sort_by_time_preserves_all_tasks` | No tasks are dropped or duplicated after sorting |
| **Recurrence** | `test_daily_recurring_task_creates_next_day_occurrence` | Completing a daily task generates a new task due tomorrow |
| | `test_daily_recurrence_preserves_time_of_day` | The next occurrence keeps the original 08:30 time-of-day |
| | `test_completing_daily_task_marks_original_complete` | The original task's status is set to `complete` |
| | `test_non_recurring_task_produces_no_next_occurrence` | Non-recurring tasks return `None` from `complete_task()` |
| | `test_monthly_recurring_task_produces_no_auto_occurrence` | Monthly tasks are not auto-generated |
| **Conflict detection** | `test_detect_conflicts_flags_same_time_tasks` | Two same-pet tasks at the same time are flagged |
| | `test_detect_conflicts_no_false_positives_outside_window` | Tasks 2 hours apart are not flagged within a 30-min window |
| | `test_detect_all_conflicts_catches_cross_pet_overlap` | Same-time tasks across different pets are detected |
| | `test_completed_tasks_excluded_from_conflict_detection` | Completed tasks are ignored during conflict checks |

---

## Confidence & Known Gaps

**Current confidence: 3 / 5 stars**

The core logic for sorting, daily recurrence, and same-pet conflict detection is well-tested and behaves correctly in all verified cases. Confidence is held back for two reasons:

1. The test suite does not yet cover `PetCareSystem`-level integration (dual-ownership sync, `remove_pet` orphan cleanup, ID assignment on recurrence) or edge cases like month-end date arithmetic and walk tracking state.
2. The two original tests only covered `mark_complete` and `add_task`, so the overall surface is still narrow relative to the full system.

Adding integration tests for `PetCareSystem` and edge-case coverage for `WalkTask` and month-end recurrence would push this to 4–5 stars.
