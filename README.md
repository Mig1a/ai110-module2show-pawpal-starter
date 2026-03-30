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
