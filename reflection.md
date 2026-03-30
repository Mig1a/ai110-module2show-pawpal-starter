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

    The scheduler considers time (due_time orders and filters every task), priority (a 1–10 score boosted +10 when overdue), status (complete tasks are excluded from conflict checks and suggestions), and recurrence pattern (daily/weekly tasks auto-regenerate after completion).

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
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
