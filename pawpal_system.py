

from datetime import datetime, date, timedelta
import copy


class Task:
    """Base class for all pet care tasks; holds shared scheduling and priority fields."""

    def __init__(self, task_id, title, category, description, due_time, priority, status, recurring, recurrence_pattern, pet_id):
        """Initialise a task with identity, scheduling, and recurrence metadata."""
        self._task_id = task_id
        self._title = title
        self._category = category
        self._description = description
        self._due_time = due_time
        self._priority = priority
        self._status = status
        self._recurring = recurring
        self._recurrence_pattern = recurrence_pattern
        self._pet_id = pet_id

    def mark_complete(self):
        """Set the task status to 'complete'."""
        self._status = 'complete'

    def mark_pending(self):
        """Reset the task status to 'pending'."""
        self._status = 'pending'

    def is_overdue(self, current_time):
        """Return True if the task is not complete and its due time has passed."""
        return self._status != 'complete' and current_time > self._due_time

    def update_details(self, title, description, due_time, priority, status):
        """Replace the task's core fields with the provided values."""
        self._title = title
        self._description = description
        self._due_time = due_time
        self._priority = priority
        self._status = status

    # FIX #5: authoritative priority score lives here; Scheduler just sorts by it.
    # Score = base priority boosted when overdue, lowered when complete.
    def calculate_priority(self):
        """Return a numeric priority score; overdue tasks score +10, complete tasks score 0."""
        score = self._priority
        if self._status == 'complete':
            return 0
        if self.is_overdue(datetime.now()):
            score += 10
        return score


class FeedingTask(Task):
    """Task subclass for scheduled feeding events; tracks food type, portion, and last-fed time."""

    def __init__(self, task_id, title, category, description, due_time, priority, status, recurring, recurrence_pattern, pet_id, food_type, portion_size, diet_notes):
        """Extend Task with feeding-specific fields: food type, portion size, and diet notes."""
        super().__init__(task_id, title, category, description, due_time, priority, status, recurring, recurrence_pattern, pet_id)
        self._food_type = food_type
        self._portion_size = portion_size
        self._diet_notes = diet_notes
        self._last_fed = None

    def record_feeding(self):
        """Timestamp the feeding and mark the task complete."""
        self._last_fed = datetime.now()
        self.mark_complete()

    def update_portion(self, size):
        """Update the portion size to the given value."""
        self._portion_size = size


class WalkTask(Task):
    """Task subclass for walks; tracks planned duration, distance goal, and actual elapsed time."""

    # FIX #4: added _start_time and _actual_duration so start/end/summary have state to work with
    def __init__(self, task_id, title, category, description, due_time, priority, status, recurring, recurrence_pattern, pet_id, duration, distance_goal, location):
        """Extend Task with walk-specific fields: duration, distance goal, location, and runtime tracking."""
        super().__init__(task_id, title, category, description, due_time, priority, status, recurring, recurrence_pattern, pet_id)
        self._duration = duration
        self._distance_goal = distance_goal
        self._location = location
        self._start_time = None       # set by start_walk()
        self._actual_duration = None  # computed by end_walk()

    def start_walk(self):
        """Record the walk start time and set status to 'in_progress'."""
        self._start_time = datetime.now()
        self._status = 'in_progress'

    def end_walk(self):
        """Calculate elapsed minutes since start_walk() and mark the task complete."""
        if self._start_time is None:
            return
        elapsed = datetime.now() - self._start_time
        self._actual_duration = int(elapsed.total_seconds() / 60)
        self.mark_complete()

    def record_walk_summary(self):
        """Return a dict of planned vs actual walk stats."""
        return {
            'location': self._location,
            'distance_goal': self._distance_goal,
            'planned_duration': self._duration,
            'actual_duration': self._actual_duration,
            'start_time': self._start_time,
        }


class MedicationTask(Task):
    """Task subclass for medication administration; tracks dosage, instructions, and refill date."""

    def __init__(self, task_id, title, category, description, due_time, priority, status, recurring, recurrence_pattern, pet_id, medication_name, dosage, instructions, refill_date):
        """Extend Task with medication-specific fields: name, dosage, instructions, and refill date."""
        super().__init__(task_id, title, category, description, due_time, priority, status, recurring, recurrence_pattern, pet_id)
        self._medication_name = medication_name
        self._dosage = dosage
        self._instructions = instructions
        self._refill_date = refill_date
        self._last_dose_time = None

    def record_dose(self):
        """Timestamp the dose administration and mark the task complete."""
        self._last_dose_time = datetime.now()
        self.mark_complete()

    def check_refill_needed(self):
        """Return True if today is on or past the refill date."""
        if self._refill_date is None:
            return False
        return date.today() >= self._refill_date

    # FIX #7: accepts sibling tasks so it can check for conflicts without needing a Pet reference
    def validate_schedule(self, all_pet_medication_tasks):
        """Return a list of medication names scheduled at the same time as this task."""
        conflicts = []
        for other in all_pet_medication_tasks:
            if other._task_id == self._task_id:
                continue
            if other._due_time == self._due_time:
                conflicts.append(other._medication_name)
        return conflicts


class AppointmentTask(Task):
    """Task subclass for vet or grooming appointments; tracks provider, location, and reminder time."""

    def __init__(self, task_id, title, category, description, due_time, priority, status, recurring, recurrence_pattern, pet_id, location, provider_name, appointment_type, contact_info, reminder_time):
        """Extend Task with appointment-specific fields: location, provider, type, contact, and reminder time."""
        super().__init__(task_id, title, category, description, due_time, priority, status, recurring, recurrence_pattern, pet_id)
        self._location = location
        self._provider_name = provider_name
        self._appointment_type = appointment_type
        self._contact_info = contact_info
        self._reminder_time = reminder_time
        self._provider_notes = []

    def reschedule(self, new_time):
        """Move the appointment and its reminder to a new datetime."""
        self._due_time = new_time
        self._reminder_time = new_time

    def add_provider_notes(self, notes):
        """Append a provider note string to the notes list."""
        self._provider_notes.append(notes)

    def send_reminder(self):
        """Print an appointment reminder with provider and location details."""
        print(f"Reminder: {self._appointment_type} with {self._provider_name} at {self._location} on {self._due_time}")


class Pet:
    """Represents a pet and owns its task list; serves as the per-pet source of truth."""

    def __init__(self, pet_id, name, species, breed, age, weight, owner_name, notes):
        """Initialise a pet profile with identity, physical, and owner fields."""
        self._pet_id = pet_id
        self._name = name
        self._species = species
        self._breed = breed
        self._age = age
        self._weight = weight
        self._owner_name = owner_name
        self._notes = notes
        # FIX #2: Pet._tasks is the single source of truth for this pet's tasks.
        # Scheduler holds references to the same objects — no copies, no drift.
        self._tasks = []

    def add_task(self, task):
        """Append a task to this pet's task list."""
        self._tasks.append(task)

    def remove_task(self, task_id):
        """Remove the task with the given ID from this pet's task list."""
        self._tasks = [t for t in self._tasks if t._task_id != task_id]

    def get_tasks(self):
        """Return a copy of all tasks belonging to this pet."""
        return list(self._tasks)

    def get_today_tasks(self):
        """Return all tasks due today for this pet."""
        today = date.today()
        return [t for t in self._tasks if t._due_time.date() == today]

    # FIX #7: convenience accessor so MedicationTask.validate_schedule() can be called
    # with Pet.get_medication_tasks() as its argument
    def get_medication_tasks(self):
        """Return only MedicationTask instances from this pet's task list."""
        return [t for t in self._tasks if isinstance(t, MedicationTask)]

    def update_profile(self, name, species, breed, age, weight, notes):
        """Overwrite the pet's profile fields with the provided values."""
        self._name = name
        self._species = species
        self._breed = breed
        self._age = age
        self._weight = weight
        self._notes = notes


class Scheduler:
    """Owns all cross-pet task logic: sorting, filtering, conflict detection, and recurrence."""

    def __init__(self):
        """Initialise the scheduler with an empty task list and today's date."""
        # FIX #2: Scheduler._tasks holds references to the same task objects that
        # live in each Pet._tasks — PetCareSystem keeps both in sync on add/remove.
        self._tasks = []
        self._priority_queue = []
        self._current_date = date.today()

    def add_task(self, task):
        """Register a task and keep the master list sorted by due time."""
        self._tasks.append(task)
        self._tasks.sort(key=lambda t: t._due_time)

    def remove_task(self, task_id):
        """Drop the task with the given ID from the scheduler's master list."""
        self._tasks = [t for t in self._tasks if t._task_id != task_id]

    # FIX #2: accepts pet_id to match PetCareSystem.view_pet_schedule signature
    def get_daily_schedule(self, pet_id, target_date):
        """Return all tasks for the given pet that are due on target_date."""
        return [
            t for t in self._tasks
            if t._pet_id == pet_id and t._due_time.date() == target_date
        ]

    def get_upcoming_tasks(self):
        """Return all incomplete tasks whose due time is in the future."""
        now = datetime.now()
        return [t for t in self._tasks if t._due_time > now and t._status != 'complete']

    def get_overdue_tasks(self):
        """Return all tasks that are past due and not yet complete."""
        now = datetime.now()
        return [t for t in self._tasks if t.is_overdue(now)]

    # --- Sorting ---

    def sort_by_time(self, tasks=None):
        """Return a list of Task objects sorted ascending by _due_time.

        Args:
            tasks: optional list of Task objects to sort.
                   Defaults to the full scheduler task list when omitted.
        Returns:
            A new sorted list; the original list is not mutated.
        """
        source = tasks if tasks is not None else self._tasks
        return sorted(source, key=lambda t: t._due_time)

    # --- Filtering ---

    def get_tasks_by_pet(self, pet_id):
        """Return all tasks for the given pet, in due-time order."""
        return [t for t in self._tasks if t._pet_id == pet_id]

    def get_tasks_by_status(self, status):
        """Return all tasks whose status matches the given value."""
        return [t for t in self._tasks if t._status == status]

    def get_tasks_by_pet_and_status(self, pet_id, status):
        """Return tasks for a specific pet filtered by status, in due-time order."""
        return [t for t in self._tasks if t._pet_id == pet_id and t._status == status]

    # --- Conflict detection ---

    def detect_conflicts(self, pet_id, window_minutes=30):
        """Return pairs of pending tasks for the given pet whose due times are
        within *window_minutes* of each other on the same day."""
        pet_tasks = [
            t for t in self._tasks
            if t._pet_id == pet_id and t._status != 'complete'
        ]
        conflicts = []
        for i in range(len(pet_tasks)):
            for j in range(i + 1, len(pet_tasks)):
                t1, t2 = pet_tasks[i], pet_tasks[j]
                if t1._due_time.date() != t2._due_time.date():
                    continue
                delta_seconds = abs((t1._due_time - t2._due_time).total_seconds())
                if delta_seconds <= window_minutes * 60:
                    conflicts.append((t1, t2))
        return conflicts

    def detect_all_conflicts(self, window_minutes=0):
        """Scan every pending task pair across ALL pets for scheduling conflicts.

        Unlike detect_conflicts() which checks a single pet, this method compares
        every combination — same-pet pairs AND cross-pet pairs — so nothing is
        missed.

        Strategy (lightweight, no exceptions raised):
          - Skip any task whose status is 'complete' — it no longer occupies a slot.
          - Skip pairs on different calendar days — no clash possible.
          - Compute the absolute time gap between the two due times.
          - If that gap is within window_minutes, record the pair.
          - window_minutes=0 (default) catches only exact same-time clashes.
            Raise it (e.g. 15) to catch near-conflicts too.

        Returns:
            List of (Task, Task) tuples — never raises, returns [] on no conflicts.
        """
        pending = [t for t in self._tasks if t._status != 'complete']
        conflicts = []
        for i in range(len(pending)):
            for j in range(i + 1, len(pending)):
                t1, t2 = pending[i], pending[j]
                if t1._due_time.date() != t2._due_time.date():
                    continue
                delta_seconds = abs((t1._due_time - t2._due_time).total_seconds())
                if delta_seconds <= window_minutes * 60:
                    conflicts.append((t1, t2))
        return conflicts

    # --- Recurring task generation ---

    def generate_next_occurrence(self, task):
        """Clone a recurring task and set its due time to the next correct occurrence.

        How timedelta is used
        ---------------------
        timedelta(days=N) represents an exact duration of N * 86 400 seconds.
        Adding it to a date gives the date N days in the future; adding it to a
        datetime shifts both the date and time by the same amount.

        For 'daily' and 'weekly' patterns we anchor to *today* rather than to the
        task's original due_time.  This matters when a task is completed late:

            task._due_time = yesterday 08:00   (overdue)
            completed today

            Wrong:  yesterday 08:00 + timedelta(days=1)  →  today 08:00
                    (next occurrence is already almost due/overdue)

            Right:  date.today() + timedelta(days=1)      →  tomorrow
                    datetime.combine(tomorrow, time(8,0))  →  tomorrow 08:00

        datetime.combine(date, time) stitches a calendar date and a clock time
        into a single datetime object, letting us change the date while keeping
        the original time-of-day intact.

        'monthly' keeps the old delta-from-due_time behaviour because it is
        excluded from auto-recurrence in complete_task() and is managed manually.

        Returns a new task object with status 'pending' and task_id reset to 0
        so PetCareSystem will assign a fresh ID via id_callback.
        """
        original_time = task._due_time.time()   # preserve e.g. 08:00, 13:00, 18:30

        if task._recurrence_pattern == 'daily':
            next_date = date.today() + timedelta(days=1)
            next_due  = datetime.combine(next_date, original_time)
        elif task._recurrence_pattern == 'weekly':
            next_date = date.today() + timedelta(weeks=1)
            next_due  = datetime.combine(next_date, original_time)
        else:
            # 'monthly' or any unknown pattern: fall back to offset from due_time
            next_due = task._due_time + timedelta(days=30)

        next_task = copy.copy(task)
        next_task._task_id = 0          # reassigned by id_callback in complete_task
        next_task._due_time = next_due
        next_task._status = 'pending'

        # Reset per-occurrence tracking fields
        if hasattr(next_task, '_last_fed'):
            next_task._last_fed = None
        if hasattr(next_task, '_last_dose_time'):
            next_task._last_dose_time = None
        if hasattr(next_task, '_start_time'):
            next_task._start_time = None
            next_task._actual_duration = None

        return next_task

    def complete_task(self, task_id, id_callback=None):
        """Mark a task complete and, for 'daily' or 'weekly' recurring tasks,
        automatically generate and register the next occurrence.

        This is the single place that owns recurrence logic for the scheduler.
        'monthly' tasks are intentionally excluded — those are managed manually.

        Args:
            task_id:     ID of the task to mark complete.
            id_callback: optional callable () -> int that returns the next unique
                         task ID.  Pass PetCareSystem._next_task_id so the new
                         task receives a proper ID before entering the list.
                         If omitted the new task keeps id=0 (useful in tests).
        Returns:
            The newly created Task for the next occurrence, or None when the
            completed task is not daily/weekly recurring.
        """
        for task in self._tasks:
            if task._task_id != task_id:
                continue
            task.mark_complete()
            if task._recurring and task._recurrence_pattern in ('daily', 'weekly'):
                next_task = self.generate_next_occurrence(task)
                if id_callback is not None:
                    next_task._task_id = id_callback()
                self._tasks.append(next_task)
                self._tasks.sort(key=lambda t: t._due_time)
                return next_task
            return None
        return None

    # FIX #5: calls task.calculate_priority() on each task and sorts; logic stays in Task
    def prioritize_tasks(self):
        """Sort all tasks by their calculated priority score (highest first) and return the list."""
        self._priority_queue = sorted(self._tasks, key=lambda t: t.calculate_priority(), reverse=True)
        return self._priority_queue

    def suggest_next_task(self):
        """Return the highest-priority pending task, or None if no tasks exist."""
        queue = self.prioritize_tasks()
        return queue[0] if queue else None


class Reminder:
    """Represents a scheduled notification for a task; supports push, email, and SMS channels."""

    # FIX #1: added pet_id so reminders can be queried per-pet without traversing tasks
    # FIX #6: added channel so send() knows how to deliver (e.g. 'push', 'email', 'sms')
    def __init__(self, reminder_id, task_id, pet_id, message, reminder_time, sent_status, channel='push'):
        """Initialise a reminder with target task, delivery channel, and scheduled send time."""
        self._reminder_id = reminder_id
        self._task_id = task_id
        self._pet_id = pet_id          # FIX #1
        self._message = message
        self._reminder_time = reminder_time
        self._sent_status = sent_status
        self._channel = channel        # FIX #6

    def generate_message(self):
        """Build and store a default reminder message string, then return it."""
        self._message = f"Reminder [{self._channel}] for task {self._task_id}: due at {self._reminder_time}"
        return self._message

    # FIX #6: dispatches via self._channel instead of hardcoded delivery logic
    def send(self):
        """Deliver the reminder via the configured channel and mark it sent."""
        if self._sent_status:
            return
        message = self._message or self.generate_message()
        if self._channel == 'push':
            print(f"[PUSH] {message}")
        elif self._channel == 'email':
            print(f"[EMAIL] {message}")
        elif self._channel == 'sms':
            print(f"[SMS] {message}")
        else:
            print(f"[{self._channel.upper()}] {message}")
        self.mark_sent()

    def mark_sent(self):
        """Flag this reminder as already sent."""
        self._sent_status = True

    def is_due(self, current_time):
        """Return True if the reminder hasn't been sent and its time has arrived."""
        return not self._sent_status and current_time >= self._reminder_time


class PetCareSystem:
    """Top-level facade; coordinates pets, the scheduler, and reminders through a single API."""

    def __init__(self):
        """Initialise the system with empty pet and reminder lists and a fresh Scheduler."""
        self._pets = []
        self._scheduler = Scheduler()
        self._reminders = []
        # FIX #3: centralised counter — all task creation goes through _next_task_id()
        self._task_id_counter = 0
        self._reminder_id_counter = 0

    # FIX #3: single place that mints unique task IDs
    def _next_task_id(self):
        """Increment and return the next unique task ID."""
        self._task_id_counter += 1
        return self._task_id_counter

    def _next_reminder_id(self):
        """Increment and return the next unique reminder ID."""
        self._reminder_id_counter += 1
        return self._reminder_id_counter

    def _find_pet(self, pet_id):
        """Return the Pet with the matching ID, or None if not found."""
        for pet in self._pets:
            if pet._pet_id == pet_id:
                return pet
        return None

    def _find_pet_by_name(self, name):
        """Return the Pet whose name matches (case-insensitive), or None if not found."""
        name_lower = name.lower()
        for pet in self._pets:
            if pet._name.lower() == name_lower:
                return pet
        return None

    def add_pet(self, pet):
        """Register a new pet with the system."""
        self._pets.append(pet)

    def remove_pet(self, pet_id):
        """Remove a pet and all its tasks from the system."""
        self._pets = [p for p in self._pets if p._pet_id != pet_id]
        self._scheduler._tasks = [t for t in self._scheduler._tasks if t._pet_id != pet_id]

    # FIX #2: single entry point that writes to BOTH Pet._tasks and Scheduler._tasks
    # so they never drift. Uses _next_task_id() to guarantee uniqueness (FIX #3).
    def add_task_to_pet(self, pet_id, task):
        """Assign a task to the given pet and register it with the scheduler."""
        pet = self._find_pet(pet_id)
        if pet is None:
            return
        task._task_id = self._next_task_id()
        task._pet_id = pet_id
        pet.add_task(task)
        self._scheduler.add_task(task)

    # FIX #2: mirrors add_task_to_pet — removes from both Pet and Scheduler
    def remove_task_from_pet(self, pet_id, task_id):
        """Remove a task from both the pet's list and the scheduler."""
        pet = self._find_pet(pet_id)
        if pet is None:
            return
        pet.remove_task(task_id)
        self._scheduler.remove_task(task_id)

    def view_pet_schedule(self, pet_id, target_date):
        """Return the scheduler's daily task list for the given pet and date."""
        return self._scheduler.get_daily_schedule(pet_id, target_date)

    def complete_task(self, task_id):
        """Complete a task and sync any auto-generated recurrence into Pet._tasks.

        Recurrence logic lives entirely in Scheduler.complete_task(); this method
        only handles the PetCareSystem concern of keeping Pet._tasks in sync with
        the scheduler.
        """
        next_task = self._scheduler.complete_task(task_id, self._next_task_id)
        if next_task is not None:
            pet = self._find_pet(next_task._pet_id)
            if pet is not None:
                pet.add_task(next_task)

    def get_system_summary(self):
        """Return a dict with counts of pets, tasks, overdue items, upcoming items, and pending reminders."""
        total_tasks = len(self._scheduler._tasks)
        overdue = len(self._scheduler.get_overdue_tasks())
        upcoming = len(self._scheduler.get_upcoming_tasks())
        return {
            'total_pets': len(self._pets),
            'total_tasks': total_tasks,
            'overdue_tasks': overdue,
            'upcoming_tasks': upcoming,
            'pending_reminders': sum(1 for r in self._reminders if not r._sent_status),
        }

    def get_pet_tasks_by_status(self, pet_id, status):
        """Return all tasks for a pet filtered by status, sorted by due time."""
        return self._scheduler.get_tasks_by_pet_and_status(pet_id, status)

    def detect_pet_conflicts(self, pet_id, window_minutes=30):
        """Return conflicting pending-task pairs for a pet within window_minutes."""
        return self._scheduler.detect_conflicts(pet_id, window_minutes)

    def get_conflict_warnings(self, window_minutes=0):
        """Return human-readable warning strings for every scheduling conflict.

        Calls Scheduler.detect_all_conflicts() for the raw pairs, then formats
        each one into a plain string.  Same-pet and cross-pet conflicts receive
        different labels so the owner can tell them apart at a glance.

        Never raises — returns an empty list when the schedule is conflict-free.

        Args:
            window_minutes: passed through to detect_all_conflicts().
                            0 = exact same time only (default).
        Returns:
            List of warning strings, one per conflicting pair.
        """
        pet_names = {p._pet_id: p._name for p in self._pets}
        pairs = self._scheduler.detect_all_conflicts(window_minutes)
        warnings = []
        for t1, t2 in pairs:
            time_str = t1._due_time.strftime('%I:%M %p')
            if t1._pet_id == t2._pet_id:
                name = pet_names.get(t1._pet_id, f'pet {t1._pet_id}')
                warnings.append(
                    f"WARNING [same-pet]  : '{t1._title}' and '{t2._title}'"
                    f" — both scheduled for {name} at {time_str}"
                )
            else:
                n1 = pet_names.get(t1._pet_id, f'pet {t1._pet_id}')
                n2 = pet_names.get(t2._pet_id, f'pet {t2._pet_id}')
                warnings.append(
                    f"WARNING [cross-pet] : '{t1._title}' ({n1}) and"
                    f" '{t2._title}' ({n2}) — both scheduled at {time_str}"
                )
        return warnings

    def filter_tasks(self, status=None, pet_name=None):
        """Return tasks filtered by completion status, pet name, or both.

        Args:
            status:   'pending', 'complete', or 'in_progress'.
                      Pass None to skip status filtering.
            pet_name: case-insensitive pet name string.
                      Pass None to include tasks for all pets.
        Returns:
            A sorted list of matching Task objects, or an empty list when
            pet_name is given but no matching pet exists.
        Raises:
            ValueError: if status is not one of the recognised values.
        """
        valid_statuses = {'pending', 'complete', 'in_progress'}
        if status is not None and status not in valid_statuses:
            raise ValueError(
                f"Unknown status '{status}'. Expected one of: {sorted(valid_statuses)}"
            )

        tasks = list(self._scheduler._tasks)

        if pet_name is not None:
            pet = self._find_pet_by_name(pet_name)
            if pet is None:
                return []
            tasks = [t for t in tasks if t._pet_id == pet._pet_id]

        if status is not None:
            tasks = [t for t in tasks if t._status == status]

        return self._scheduler.sort_by_time(tasks)

    # FIX #7: helper that collects a pet's MedicationTasks so validate_schedule()
    # can be called with the full sibling list
    def validate_pet_medication_schedule(self, pet_id):
        """Return a dict mapping medication names to conflicting medication names for the given pet."""
        pet = self._find_pet(pet_id)
        if pet is None:
            return {}
        med_tasks = pet.get_medication_tasks()
        conflicts = {}
        for task in med_tasks:
            result = task.validate_schedule(med_tasks)
            if result:
                conflicts[task._medication_name] = result
        return conflicts
