from datetime import datetime, date
from pawpal_system import (
    Pet, PetCareSystem,
    FeedingTask, WalkTask, MedicationTask, AppointmentTask
)

# ---------------------------------------------------------------------------
# Setup — owner and pets
# ---------------------------------------------------------------------------
system = PetCareSystem()

owner_name = "Jordan Rivera"

buddy = Pet(
    pet_id=1,
    name="Buddy",
    species="Dog",
    breed="Golden Retriever",
    age=3,
    weight=65.0,
    owner_name=owner_name,
    notes="Loves fetch, allergic to chicken"
)

luna = Pet(
    pet_id=2,
    name="Luna",
    species="Cat",
    breed="Siamese",
    age=5,
    weight=9.5,
    owner_name=owner_name,
    notes="Indoor only, sensitive stomach"
)

system.add_pet(buddy)
system.add_pet(luna)

# ---------------------------------------------------------------------------
# Tasks — three different times today
# ---------------------------------------------------------------------------
today = date.today()

morning   = datetime(today.year, today.month, today.day,  8,  0)
afternoon = datetime(today.year, today.month, today.day, 13,  0)
evening   = datetime(today.year, today.month, today.day, 18, 30)

# Task 1 — Buddy morning feeding (8:00 AM)
buddy_breakfast = FeedingTask(
    task_id=0,           # overwritten by PetCareSystem
    title="Buddy Breakfast",
    category="Feeding",
    description="Morning kibble serving",
    due_time=morning,
    priority=3,
    status="pending",
    recurring=True,
    recurrence_pattern="daily",
    pet_id=buddy._pet_id,
    food_type="Dry kibble",
    portion_size="2 cups",
    diet_notes="No chicken-based food"
)

# Task 2 — Buddy afternoon walk (1:00 PM)
buddy_walk = WalkTask(
    task_id=0,
    title="Buddy Afternoon Walk",
    category="Exercise",
    description="30-minute neighbourhood walk",
    due_time=afternoon,
    priority=2,
    status="pending",
    recurring=True,
    recurrence_pattern="daily",
    pet_id=buddy._pet_id,
    duration=30,
    distance_goal=1.5,
    location="Neighbourhood park"
)

# Task 3 — Luna evening medication (6:30 PM)
luna_meds = MedicationTask(
    task_id=0,
    title="Luna Evening Medication",
    category="Medication",
    description="Administer digestive supplement",
    due_time=evening,
    priority=5,
    status="pending",
    recurring=True,
    recurrence_pattern="daily",
    pet_id=luna._pet_id,
    medication_name="ProBiotica",
    dosage="1 tablet",
    instructions="Hide in wet food",
    refill_date=date(today.year, today.month + 1, 1)
)

# Task 4 — Luna vet appointment (afternoon)
luna_vet = AppointmentTask(
    task_id=0,
    title="Luna Vet Checkup",
    category="Appointment",
    description="Annual wellness exam",
    due_time=afternoon,
    priority=4,
    status="pending",
    recurring=False,
    recurrence_pattern="",
    pet_id=luna._pet_id,
    location="PawCare Animal Clinic",
    provider_name="Dr. Patel",
    appointment_type="Wellness Exam",
    contact_info="555-0192",
    reminder_time=datetime(today.year, today.month, today.day, 12, 0)
)

# Task 5 — Buddy medication intentionally at 1:00 PM (same as buddy_walk and luna_vet)
# Creates a same-pet conflict (Buddy has two tasks at 1 PM) AND
# a cross-pet conflict (Buddy and Luna both have tasks at 1 PM).
buddy_noon_meds = MedicationTask(
    task_id=0,
    title="Buddy Noon Medication",
    category="Medication",
    description="Post-walk joint supplement",
    due_time=afternoon,            # 1:00 PM — deliberate collision
    priority=4,
    status="pending",
    recurring=True,
    recurrence_pattern="daily",
    pet_id=buddy._pet_id,
    medication_name="FlexiJoint",
    dosage="1 chew",
    instructions="Give with food",
    refill_date=date(today.year, today.month + 1, 1) if today.month < 12
                else date(today.year + 1, 1, 1)
)

# Registered intentionally out of chronological order to prove sort_by_time() works.
# Insertion order: 6:30 PM → 1:00 PM → 8:00 AM → 1:00 PM → 1:00 PM (conflict task)
system.add_task_to_pet(luna._pet_id,  luna_meds)        # 6:30 PM — latest first
system.add_task_to_pet(luna._pet_id,  luna_vet)         # 1:00 PM
system.add_task_to_pet(buddy._pet_id, buddy_breakfast)  # 8:00 AM — earliest last
system.add_task_to_pet(buddy._pet_id, buddy_walk)       # 1:00 PM
system.add_task_to_pet(buddy._pet_id, buddy_noon_meds)  # 1:00 PM — intentional conflict

# ---------------------------------------------------------------------------
# Print Today's Schedule
# ---------------------------------------------------------------------------
def print_schedule():
    print("=" * 50)
    print(f"  PAWPAL — TODAY'S SCHEDULE  ({today})")
    print(f"  Owner: {owner_name}")
    print("=" * 50)

    for pet in system._pets:
        # Tasks are kept sorted by due time in the scheduler
        tasks = system.view_pet_schedule(pet._pet_id, today)

        print(f"\n  {pet._name} ({pet._breed})")
        print(f"  {'-' * 44}")

        if not tasks:
            print("    No tasks scheduled for today.")
            continue

        for task in tasks:
            time_str  = task._due_time.strftime("%I:%M %p")
            status    = task._status.upper()
            print(f"    [{time_str}]  {task._title}")
            print(f"               Category : {task._category}")
            print(f"               Priority : {task._priority}  |  Status: {status}")

            if isinstance(task, FeedingTask):
                print(f"               Food     : {task._food_type}, {task._portion_size}")
            if isinstance(task, WalkTask):
                print(f"               Goal     : {task._distance_goal} mi, {task._duration} min")
            if isinstance(task, MedicationTask):
                print(f"               Med      : {task._medication_name} — {task._dosage}")
                if task.check_refill_needed():
                    print("               *** REFILL NEEDED ***")
            if isinstance(task, AppointmentTask):
                print(f"               Provider : {task._provider_name} @ {task._location}")

        # Conflict detection — flag tasks within 30 minutes of each other
        conflicts = system.detect_pet_conflicts(pet._pet_id, window_minutes=30)
        if conflicts:
            print(f"\n  *** SCHEDULE CONFLICTS ***")
            for t1, t2 in conflicts:
                print(f"    {t1._title} ({t1._due_time.strftime('%I:%M %p')}) "
                      f"<-> {t2._title} ({t2._due_time.strftime('%I:%M %p')})")

    print()
    print("=" * 50)
    summary = system.get_system_summary()
    print(f"  Total pets    : {summary['total_pets']}")
    print(f"  Total tasks   : {summary['total_tasks']}")
    print(f"  Overdue tasks : {summary['overdue_tasks']}")
    print(f"  Upcoming      : {summary['upcoming_tasks']}")
    print("=" * 50)


def print_demo():
    """Demonstrate sort_by_time() and filter_tasks() in the terminal."""

    def show(tasks):
        """Print a compact one-line summary for each task."""
        if not tasks:
            print("    (none)")
            return
        for t in tasks:
            print(f"    [{t._due_time.strftime('%I:%M %p')}]  "
                  f"{t._title:<32}  status={t._status}")

    # ------------------------------------------------------------------
    # DEMO 1 — sort_by_time()
    # Tasks were registered in the order: 6:30 PM, 1:00 PM, 8:00 AM, 1:00 PM
    # After sorting they must appear earliest-first.
    # ------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("  DEMO 1 — sort_by_time()  (registered out of order)")
    print("=" * 50)
    show(system._scheduler.sort_by_time())

    # ------------------------------------------------------------------
    # DEMO 2 — filter by status only
    # ------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("  DEMO 2 — filter_tasks(status='pending')")
    print("=" * 50)
    show(system.filter_tasks(status='pending'))

    # ------------------------------------------------------------------
    # DEMO 3 — filter by pet name only
    # ------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("  DEMO 3 — filter_tasks(pet_name='Buddy')")
    print("=" * 50)
    show(system.filter_tasks(pet_name='Buddy'))

    print("\n" + "=" * 50)
    print("  DEMO 4 — filter_tasks(pet_name='Luna')")
    print("=" * 50)
    show(system.filter_tasks(pet_name='Luna'))

    # ------------------------------------------------------------------
    # DEMO 5 — filter by both status and pet name
    # ------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("  DEMO 5 — filter_tasks(status='pending', pet_name='Luna')")
    print("=" * 50)
    show(system.filter_tasks(status='pending', pet_name='Luna'))

    # ------------------------------------------------------------------
    # DEMO 6 — complete a recurring task, then filter for 'complete'
    # completing buddy_breakfast also auto-schedules tomorrow's copy
    # ------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("  DEMO 6 — complete a task → filter_tasks(status='complete')")
    print("=" * 50)
    system.complete_task(buddy_breakfast._task_id)
    print(f"  '{buddy_breakfast._title}' marked complete."
          f"  (next daily occurrence auto-scheduled)")
    show(system.filter_tasks(status='complete'))

    # ------------------------------------------------------------------
    # DEMO 7 — case-insensitive pet name and unknown-name guard
    # ------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("  DEMO 7 — case-insensitive name + unknown pet returns []")
    print("=" * 50)
    print("  filter_tasks(pet_name='buddy')  ← lowercase")
    show(system.filter_tasks(pet_name='buddy'))
    print("  filter_tasks(pet_name='Max')    ← not in system")
    show(system.filter_tasks(pet_name='Max'))


def print_conflict_demo():
    """Verify that Scheduler detects same-pet and cross-pet conflicts."""
    print("\n" + "=" * 50)
    print("  CONFLICT DETECTION")
    print("=" * 50)

    # Exact same-time clashes (window_minutes=0)
    print("\n  -- Exact same-time conflicts --")
    exact = system.get_conflict_warnings(window_minutes=0)
    if exact:
        for w in exact:
            print(f"  {w}")
    else:
        print("  No exact conflicts found.")

    # Wider net: any two tasks within 30 minutes of each other
    print("\n  -- Tasks within 30 minutes of each other --")
    near = system.get_conflict_warnings(window_minutes=30)
    if near:
        for w in near:
            print(f"  {w}")
    else:
        print("  No near-conflicts found.")

    print("=" * 50)


if __name__ == "__main__":
    print_schedule()
    print_conflict_demo()
    print_demo()
