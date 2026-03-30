# PawPal+ Project Reflection

## 1. System Design
    1. Add and Manage Pet Care Tasks

    Users can create and organize all of their pet’s daily care activities in one place. This includes adding tasks such as feeding times, walks, medications, and vet appointments. Each task can include details like time, frequency, and special notes. Users can also update or remove tasks as their pet’s routine changes.

    2. View and Track the Daily Schedule

    Users can easily view their pet’s daily schedule to understand what needs to be done and when. The system displays upcoming tasks in an organized way, allowing users to track which tasks are pending, completed, or overdue. This helps ensure that no important activity is missed throughout the day.

    3. Receive Smart Prioritization and Reminders

    The system automatically organizes tasks based on urgency and importance. Time-sensitive tasks, such as medications, are prioritized over less critical ones. If a task becomes overdue, the system highlights it and brings it to the user’s attention. This helps users focus on what matters most and take timely action to care for their pet.


**a. Initial design**

- Briefly describe your initial UML design.

     PetCareSystem acts as the main controller, managing pets, tasks, scheduling, and reminders.

- What classes did you include, and what responsibilities did you assign to each?
    Pet stores pet information and its associated tasks.
    Task is the base class for all activities, handling shared data like time, status, and priority, while subclasses (Feeding, Walk, Medication, Appointment) handle specific behaviors.
    Scheduler organizes and prioritizes tasks, including identifying overdue items and suggesting the next task.
    Reminder manages notifications for upcoming or missed tasks.

**b. Design changes**

- Did your design change during implementation?
    Yes.
- If yes, describe at least one change and why you made it.
    Fix 1: Added pet_id to Reminder so reminders can be linked directly to pets.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

    1. Time — the primary constraint. Every task has a _due_time
    2. Priority — a numeric score (1–10) set per task.
    3. Status — pending, in_progress, and complete act as a soft constraint.
    4. Recurrence pattern — daily and weekly tasks automatically regenerate after completion.
    

- How did you decide which constraints mattered most?

    Time first — without it there's no schedule. Priority second — not all tasks have equal consequences if missed. Status followed naturally from both, and recurrence was added last as a usability improvement.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

    The scheduler detects conflicts by comparing due times as single points in time rather than as durations. Two tasks are flagged as conflicting only when their `_due_time` values are within a configurable `window_minutes` of each other (defaulting to 0 for exact matches). It does not model how long a task actually takes — a 30-minute walk and a medication dose scheduled 10 minutes apart will only be flagged if the window is set to at least 10, regardless of whether the walk would still be in progress when the medication is due.

- Why is that tradeoff reasonable for this scenario?

    For a personal pet care app, task durations are often informal and variable — a "30-minute walk" might run 20 minutes or 45 depending on the day. Modeling precise overlap would require storing both a start time and an end time for every task, adding complexity without much reliability gain. The point-in-time approach with an adjustable window is simpler to implement, easier for an owner to reason about ("anything within 15 minutes of each other gets flagged"), and still catches the most common real-world problem: two things accidentally booked at the exact same time. If duration-aware conflict detection became important, the `window_minutes` parameter already provides a natural upgrade path — the owner can widen the window to approximate overlap without redesigning the data model.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

    I used AI tools throughout the project for design brainstorming, code scaffolding, and refinement. Early on, I used AI to help identify the core objects (like Pet, Task, Scheduler) and define their responsibilities, which guided my UML and overall architecture. I also used it to generate initial class skeletons and structure the system in a clean, modular way.
- What kinds of prompts or questions were most helpful?

    During development, AI was helpful for debugging and refactoring. I asked it to review my design for potential issues, which led to improvements like centralizing ID generation, fixing task list synchronization, and clarifying responsibility between classes.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

    Fourteen tests across four areas: basic task operations (`mark_complete`, `add_task`), sorting correctness (`sort_by_time` returns chronological order, handles an empty list, preserves all tasks), recurrence logic (daily task generates a next occurrence due tomorrow with the original time-of-day preserved, original is marked complete, non-recurring and monthly tasks produce no auto-occurrence), and conflict detection (same-pet overlap flagged, no false positives outside the window, cross-pet clashes caught, completed tasks excluded).

- Why were these tests important?

    Sorting and conflict detection are the two features users see directly in the UI — a silent sort bug or a missed conflict would immediately undermine trust. Recurrence is the most stateful logic in the system: completing one task creates another, which means a bug compounds with every completion. Testing these three behaviors together covers the paths most likely to fail quietly.

**b. Confidence**

- How confident are you that your scheduler works correctly?

    Moderately confident — roughly 3 out of 5. The core per-method logic (sort, daily recurrence, same-pet and cross-pet conflict detection) passes all 14 tests and behaves as designed. Confidence is limited because the `PetCareSystem` integration layer — which keeps `Pet._tasks` and `Scheduler._tasks` in sync — has no dedicated tests. A bug there, such as a task surviving `remove_pet` in one list but not the other, would not be caught by the current suite.

- What edge cases would you test next if you had more time?

    The highest-priority gaps are: (1) `remove_pet` leaves no orphaned tasks in the scheduler, (2) completing a recurring task assigns it a fresh unique ID rather than keeping `id=0`, (3) a daily task due on February 28 rolls correctly to March 1, and (4) calling `end_walk()` before `start_walk()` does not crash or produce a negative duration.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

    The scheduling architecture. Keeping `Pet._tasks` and `Scheduler._tasks` as shared references — coordinated through `PetCareSystem` as a single guardian — meant that sorting, conflict detection, and recurrence all operated on the same objects without copying or syncing data manually. Once that pattern was in place, adding new features felt additive rather than risky, because there was one clear place to make each change.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

    I would replace the point-in-time conflict model with duration-aware conflict detection. Right now, a 30-minute walk and a medication dose 10 minutes later are only flagged if `window_minutes` is set to at least 10 — the system has no concept of how long a task actually takes. Adding a `_duration` field to the base `Task` class and comparing `due_time + duration` against the next task's `due_time` would catch real overlaps without requiring the user to tune a window manually. I would also add integration tests for `PetCareSystem` before extending any more features, since the sync layer is currently the largest untested surface in the system.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

    AI is most useful when you already have a clear question. Vague prompts like "help me design a scheduler" produced broad suggestions that needed heavy filtering. Specific prompts like "what breaks if two lists hold references to the same task objects" produced precise, actionable answers. The quality of AI output is directly proportional to the clarity of the problem you hand it — which means the most important skill is still being able to define the problem yourself before asking for help.
