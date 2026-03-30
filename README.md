# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Smarter Scheduling

Beyond basic task storage, `pawpal_system.py` implements four scheduling features
that make the planner genuinely useful.

### 1. Time-sorted display
`Scheduler.sort_by_time()` returns any task list sorted ascending by due time.
Tasks can be added in any order — the schedule always renders earliest-first.

### 2. Flexible task filtering
`PetCareSystem.filter_tasks(status, pet_name)` lets the UI or terminal query tasks
by completion status (`pending` / `complete` / `in_progress`), by pet name
(case-insensitive), or both at once. An unknown pet name returns `[]` instead of
raising an error.

### 3. Conflict detection
`Scheduler.detect_conflicts(pet_id, window_minutes)` flags same-pet tasks whose
due times overlap within a configurable window.
`Scheduler.detect_all_conflicts(window_minutes)` extends this to every task pair
across all pets, catching cross-pet scheduling clashes too.
`PetCareSystem.get_conflict_warnings()` formats raw conflict pairs into
human-readable strings labelled `[same-pet]` or `[cross-pet]`.

### 4. Automatic recurrence
When a `daily` or `weekly` recurring task is completed,
`Scheduler.generate_next_occurrence()` clones it and advances the due date by the
correct interval — anchored to *today* rather than the original due time so late
completions don't create near-immediate follow-ups.
The new occurrence is automatically inserted into both the scheduler and the pet's
task list via `PetCareSystem.complete_task()`.

## Testing PawPal+

### Running the test suite

```bash
python -m pytest tests/test_pawpal.py -v
```

Or run the file directly without pytest installed:

```bash
python tests/test_pawpal.py
```

### What the tests cover

| Category | Tests | What is verified |
|---|---|---|
| **Task basics** | `test_mark_complete_changes_status` | `mark_complete()` flips status to `complete` |
| | `test_add_task_increases_pet_task_count` | `Pet.add_task()` increases the pet's task count by exactly 1 |
| **Sorting correctness** | `test_sort_by_time_returns_chronological_order` | Tasks added in random order come back earliest-first |
| | `test_sort_by_time_empty_list` | Sorting an empty scheduler returns `[]` without raising |
| | `test_sort_by_time_preserves_all_tasks` | No tasks are dropped or duplicated after sorting |
| **Recurrence logic** | `test_daily_recurring_task_creates_next_day_occurrence` | Completing a daily task generates a new task due tomorrow |
| | `test_daily_recurrence_preserves_time_of_day` | The next occurrence keeps the original 08:30 time-of-day |
| | `test_completing_daily_task_marks_original_complete` | The original task's status is set to `complete` |
| | `test_non_recurring_task_produces_no_next_occurrence` | Non-recurring tasks return `None` from `complete_task()` |
| | `test_monthly_recurring_task_produces_no_auto_occurrence` | Monthly tasks are not auto-generated (managed manually) |
| **Conflict detection** | `test_detect_conflicts_flags_same_time_tasks` | Two same-pet tasks at the same time are flagged |
| | `test_detect_conflicts_no_false_positives_outside_window` | Tasks 2 hours apart are not flagged within a 30-min window |
| | `test_detect_all_conflicts_catches_cross_pet_overlap` | Same-time tasks across different pets are detected |
| | `test_completed_tasks_excluded_from_conflict_detection` | Completed tasks are ignored during conflict checks |

### Confidence Level

**3 / 5 stars**

The core logic for sorting, daily recurrence, and same-pet conflict detection is well-tested and behaves correctly in all verified cases. Confidence is held back from higher ratings for two reasons: (1) the existing suite does not yet cover `PetCareSystem`-level integration (dual ownership sync, `remove_pet` orphan cleanup, ID assignment on recurrence) or edge cases like month-end date arithmetic and walk tracking state; (2) the two original tests only covered `mark_complete` and `add_task`, so the overall test surface is still narrow relative to the full system. Adding integration tests for `PetCareSystem` would push this to 4–5 stars.
