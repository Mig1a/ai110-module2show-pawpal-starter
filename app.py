import streamlit as st
from datetime import datetime, date, time
from pawpal_system import (
    Pet,
    PetCareSystem,
    Task,
    FeedingTask,
    WalkTask,
    MedicationTask,
    AppointmentTask,
    Scheduler,
    Reminder,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ---------------------------------------------------------------------------
# Session state vault — initialise once, survive every rerun
# ---------------------------------------------------------------------------
if "system" not in st.session_state:
    st.session_state.system = PetCareSystem()

if "active_pet_id" not in st.session_state:
    st.session_state.active_pet_id = None

system: PetCareSystem = st.session_state.system

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🐾 PawPal+")
st.caption("Pet care planning assistant")
st.divider()

# ---------------------------------------------------------------------------
# Section 1 — Owner & Pet setup
# ---------------------------------------------------------------------------
st.subheader("1. Owner & Pet")

with st.form("pet_form"):
    col1, col2 = st.columns(2)
    with col1:
        owner_name = st.text_input("Owner name", value="Jordan Rivera")
        pet_name   = st.text_input("Pet name",   value="Buddy")
        species    = st.selectbox("Species", ["Dog", "Cat", "Bird", "Other"])
    with col2:
        breed  = st.text_input("Breed",  value="Golden Retriever")
        age    = st.number_input("Age (years)", min_value=0, max_value=30, value=3)
        weight = st.number_input("Weight (lbs)", min_value=0.1, max_value=300.0, value=65.0)
    notes = st.text_area("Pet notes (allergies, diet, etc.)", value="")

    add_pet = st.form_submit_button("Add Pet")

if add_pet:
    # Mint a new pet ID based on how many pets already exist
    new_id = len(system._pets) + 1
    pet = Pet(
        pet_id=new_id,
        name=pet_name,
        species=species,
        breed=breed,
        age=age,
        weight=weight,
        owner_name=owner_name,
        notes=notes,
    )
    system.add_pet(pet)
    st.session_state.active_pet_id = new_id
    st.success(f"Added {pet_name} ({species}) for owner {owner_name}.")

# Pet selector (if more than one pet exists)
if system._pets:
    pet_options = {p._name: p._pet_id for p in system._pets}
    selected_name = st.selectbox("Active pet", list(pet_options.keys()))
    st.session_state.active_pet_id = pet_options[selected_name]

st.divider()

# ---------------------------------------------------------------------------
# Section 2 — Add a task
# ---------------------------------------------------------------------------
st.subheader("2. Add a Task")

task_category = st.selectbox("Task type", ["Feeding", "Walk", "Medication", "Appointment"])

with st.form("task_form"):
    title       = st.text_input("Task title", value="Morning feeding")
    description = st.text_area("Description", value="")
    due_date    = st.date_input("Due date", value=date.today())
    due_time_val = st.time_input("Due time", value=time(8, 0))
    priority    = st.slider("Priority (1 = low, 10 = high)", 1, 10, 5)
    recurring   = st.checkbox("Recurring?")
    recurrence_pattern = st.text_input("Recurrence pattern (e.g. daily)", value="") if recurring else ""

    # Category-specific fields
    if task_category == "Feeding":
        food_type    = st.text_input("Food type",    value="Dry kibble")
        portion_size = st.text_input("Portion size", value="2 cups")
        diet_notes   = st.text_input("Diet notes",   value="")

    elif task_category == "Walk":
        duration      = st.number_input("Planned duration (min)", min_value=1, max_value=240, value=30)
        distance_goal = st.number_input("Distance goal (miles)",  min_value=0.1, max_value=20.0, value=1.0)
        location      = st.text_input("Location", value="Neighbourhood park")

    elif task_category == "Medication":
        medication_name = st.text_input("Medication name", value="")
        dosage          = st.text_input("Dosage",          value="")
        instructions    = st.text_input("Instructions",    value="")
        refill_date     = st.date_input("Refill date", value=date.today())

    elif task_category == "Appointment":
        location         = st.text_input("Location",         value="")
        provider_name    = st.text_input("Provider name",    value="")
        appointment_type = st.text_input("Appointment type", value="Wellness Exam")
        contact_info     = st.text_input("Contact info",     value="")
        reminder_hour    = st.number_input("Reminder hour (0–23)", min_value=0, max_value=23, value=8)

    add_task = st.form_submit_button("Add Task")

if add_task:
    if st.session_state.active_pet_id is None:
        st.warning("Please add a pet first.")
    else:
        due_dt = datetime.combine(due_date, due_time_val)

        if task_category == "Feeding":
            task = FeedingTask(
                task_id=0, title=title, category=task_category,
                description=description, due_time=due_dt,
                priority=priority, status="pending",
                recurring=recurring, recurrence_pattern=recurrence_pattern,
                pet_id=st.session_state.active_pet_id,
                food_type=food_type, portion_size=portion_size, diet_notes=diet_notes,
            )
        elif task_category == "Walk":
            task = WalkTask(
                task_id=0, title=title, category=task_category,
                description=description, due_time=due_dt,
                priority=priority, status="pending",
                recurring=recurring, recurrence_pattern=recurrence_pattern,
                pet_id=st.session_state.active_pet_id,
                duration=duration, distance_goal=distance_goal, location=location,
            )
        elif task_category == "Medication":
            task = MedicationTask(
                task_id=0, title=title, category=task_category,
                description=description, due_time=due_dt,
                priority=priority, status="pending",
                recurring=recurring, recurrence_pattern=recurrence_pattern,
                pet_id=st.session_state.active_pet_id,
                medication_name=medication_name, dosage=dosage,
                instructions=instructions, refill_date=refill_date,
            )
        elif task_category == "Appointment":
            reminder_dt = datetime.combine(due_date, time(reminder_hour, 0))
            task = AppointmentTask(
                task_id=0, title=title, category=task_category,
                description=description, due_time=due_dt,
                priority=priority, status="pending",
                recurring=recurring, recurrence_pattern=recurrence_pattern,
                pet_id=st.session_state.active_pet_id,
                location=location, provider_name=provider_name,
                appointment_type=appointment_type, contact_info=contact_info,
                reminder_time=reminder_dt,
            )

        system.add_task_to_pet(st.session_state.active_pet_id, task)
        st.success(f"Task '{title}' added.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Today's Schedule
# ---------------------------------------------------------------------------
st.subheader("3. Today's Schedule")

if st.button("Generate Schedule"):
    if not system._pets:
        st.warning("No pets in the system yet.")
    else:
        for pet in system._pets:
            tasks = system.view_pet_schedule(pet._pet_id, date.today())
            tasks_sorted = sorted(tasks, key=lambda t: t._due_time)

            st.markdown(f"#### {pet._name} — {pet._breed}")

            if not tasks_sorted:
                st.info("No tasks scheduled for today.")
                continue

            for task in tasks_sorted:
                status_icon = "✅" if task._status == "complete" else "🕐"
                with st.container(border=True):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.markdown(f"**{status_icon} {task._due_time.strftime('%I:%M %p')} — {task._title}**")
                        st.caption(f"Category: {task._category} | Priority: {task._priority} | Status: {task._status}")
                        if task._description:
                            st.write(task._description)

                        # Category-specific detail lines
                        if hasattr(task, "_food_type"):
                            st.write(f"Food: {task._food_type}, {task._portion_size}")
                        if hasattr(task, "_distance_goal"):
                            st.write(f"Goal: {task._distance_goal} mi over {task._duration} min @ {task._location}")
                        if hasattr(task, "_medication_name"):
                            st.write(f"Medication: {task._medication_name} — {task._dosage}")
                            if task.check_refill_needed():
                                st.warning("Refill needed!")
                        if hasattr(task, "_provider_name"):
                            st.write(f"Provider: {task._provider_name} @ {task._location}")

                    with col_b:
                        if task._status != "complete":
                            if st.button("Mark done", key=f"done_{task._task_id}"):
                                system.complete_task(task._task_id)
                                st.rerun()

        st.divider()
        summary = system.get_system_summary()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Pets",     summary["total_pets"])
        col2.metric("Tasks",    summary["total_tasks"])
        col3.metric("Overdue",  summary["overdue_tasks"])
        col4.metric("Upcoming", summary["upcoming_tasks"])
