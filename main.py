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

system.add_task_to_pet(buddy._pet_id, buddy_breakfast)
system.add_task_to_pet(buddy._pet_id, buddy_walk)
system.add_task_to_pet(luna._pet_id,  luna_meds)
system.add_task_to_pet(luna._pet_id,  luna_vet)

# ---------------------------------------------------------------------------
# Print Today's Schedule
# ---------------------------------------------------------------------------
def print_schedule():
    print("=" * 50)
    print(f"  PAWPAL — TODAY'S SCHEDULE  ({today})")
    print(f"  Owner: {owner_name}")
    print("=" * 50)

    for pet in system._pets:
        tasks = system.view_pet_schedule(pet._pet_id, today)
        tasks_sorted = sorted(tasks, key=lambda t: t._due_time)

        print(f"\n  {pet._name} ({pet._breed})")
        print(f"  {'-' * 44}")

        if not tasks_sorted:
            print("    No tasks scheduled for today.")
            continue

        for task in tasks_sorted:
            time_str  = task._due_time.strftime("%I:%M %p")
            status    = task._status.upper()
            print(f"    [{time_str}]  {task._title}")
            print(f"               Category : {task._category}")
            print(f"               Priority : {task._priority}  |  Status: {status}")

            if hasattr(task, '_food_type'):
                print(f"               Food     : {task._food_type}, {task._portion_size}")
            if hasattr(task, '_distance_goal'):
                print(f"               Goal     : {task._distance_goal} mi, {task._duration} min")
            if hasattr(task, '_medication_name'):
                print(f"               Med      : {task._medication_name} — {task._dosage}")
                if task.check_refill_needed():
                    print("               *** REFILL NEEDED ***")
            if hasattr(task, '_provider_name'):
                print(f"               Provider : {task._provider_name} @ {task._location}")

    print()
    print("=" * 50)
    summary = system.get_system_summary()
    print(f"  Total pets    : {summary['total_pets']}")
    print(f"  Total tasks   : {summary['total_tasks']}")
    print(f"  Overdue tasks : {summary['overdue_tasks']}")
    print(f"  Upcoming      : {summary['upcoming_tasks']}")
    print("=" * 50)


if __name__ == "__main__":
    print_schedule()
