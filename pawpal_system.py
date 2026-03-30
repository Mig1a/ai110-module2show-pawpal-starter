

from datetime import datetime, date


class Task:
    def __init__(self, task_id, title, category, description, due_time, priority, status, recurring, recurrence_pattern, pet_id):
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
    def __init__(self, task_id, title, category, description, due_time, priority, status, recurring, recurrence_pattern, pet_id, food_type, portion_size, diet_notes):
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
    # FIX #4: added _start_time and _actual_duration so start/end/summary have state to work with
    def __init__(self, task_id, title, category, description, due_time, priority, status, recurring, recurrence_pattern, pet_id, duration, distance_goal, location):
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
    def __init__(self, task_id, title, category, description, due_time, priority, status, recurring, recurrence_pattern, pet_id, medication_name, dosage, instructions, refill_date):
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
    def __init__(self, task_id, title, category, description, due_time, priority, status, recurring, recurrence_pattern, pet_id, location, provider_name, appointment_type, contact_info, reminder_time):
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
    def __init__(self, pet_id, name, species, breed, age, weight, owner_name, notes):
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
    def __init__(self):
        # FIX #2: Scheduler._tasks holds references to the same task objects that
        # live in each Pet._tasks — PetCareSystem keeps both in sync on add/remove.
        self._tasks = []
        self._priority_queue = []
        self._current_date = date.today()

    def add_task(self, task):
        """Register a task object in the scheduler's master list."""
        self._tasks.append(task)

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
    # FIX #1: added pet_id so reminders can be queried per-pet without traversing tasks
    # FIX #6: added channel so send() knows how to deliver (e.g. 'push', 'email', 'sms')
    def __init__(self, reminder_id, task_id, pet_id, message, reminder_time, sent_status, channel='push'):
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
    def __init__(self):
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
        """Find the task by ID across all pets and mark it complete."""
        for task in self._scheduler._tasks:
            if task._task_id == task_id:
                task.mark_complete()
                return

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
