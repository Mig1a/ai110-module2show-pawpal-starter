import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime
from pawpal_system import Task, Pet


def test_mark_complete_changes_status():
    """Task Completion: mark_complete() should set status to 'complete'."""
    task = Task(
        task_id=1,
        title="Test Task",
        category="General",
        description="A test task",
        due_time=datetime(2026, 3, 30, 9, 0),
        priority=2,
        status="pending",
        recurring=False,
        recurrence_pattern="",
        pet_id=1
    )

    assert task._status == "pending"
    task.mark_complete()
    assert task._status == "complete"


def test_add_task_increases_pet_task_count():
    """Task Addition: adding a task to a Pet should increase its task count by 1."""
    pet = Pet(
        pet_id=1,
        name="Buddy",
        species="Dog",
        breed="Golden Retriever",
        age=3,
        weight=65.0,
        owner_name="Jordan Rivera",
        notes=""
    )

    task = Task(
        task_id=1,
        title="Morning Walk",
        category="Exercise",
        description="Walk around the block",
        due_time=datetime(2026, 3, 30, 8, 0),
        priority=2,
        status="pending",
        recurring=False,
        recurrence_pattern="",
        pet_id=1
    )

    before = len(pet.get_tasks())
    pet.add_task(task)
    after = len(pet.get_tasks())

    assert after == before + 1


def _make_task(task_id, pet_id, due_time, priority=3, status="pending",
               recurring=False, recurrence_pattern=""):
    """Helper: create a plain Task with sensible defaults."""
    return Task(
        task_id=task_id,
        title=f"Task {task_id}",
        category="General",
        description="",
        due_time=due_time,
        priority=priority,
        status=status,
        recurring=recurring,
        recurrence_pattern=recurrence_pattern,
        pet_id=pet_id,
    )


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """sort_by_time() must return tasks ordered earliest → latest."""
    from pawpal_system import Scheduler

    scheduler = Scheduler()
    t1 = _make_task(1, 1, datetime(2026, 4, 1, 14, 0))
    t2 = _make_task(2, 1, datetime(2026, 4, 1,  8, 0))
    t3 = _make_task(3, 1, datetime(2026, 4, 1, 11, 0))
    for t in [t1, t2, t3]:
        scheduler.add_task(t)

    sorted_tasks = scheduler.sort_by_time()
    due_times = [t._due_time for t in sorted_tasks]

    assert due_times == sorted(due_times), "Tasks are not in ascending due-time order"


def test_sort_by_time_empty_list():
    """sort_by_time() on an empty list must return [] without raising."""
    from pawpal_system import Scheduler

    scheduler = Scheduler()
    result = scheduler.sort_by_time()

    assert result == []


def test_sort_by_time_preserves_all_tasks():
    """sort_by_time() must not drop or duplicate any tasks."""
    from pawpal_system import Scheduler

    scheduler = Scheduler()
    tasks = [
        _make_task(i, 1, datetime(2026, 4, 1, h, 0))
        for i, h in enumerate([9, 7, 15, 11, 6], start=1)
    ]
    for t in tasks:
        scheduler.add_task(t)

    sorted_tasks = scheduler.sort_by_time()

    assert len(sorted_tasks) == len(tasks)


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_daily_recurring_task_creates_next_day_occurrence():
    """Completing a daily recurring task must generate one new task due tomorrow."""
    from pawpal_system import Scheduler
    from datetime import date, timedelta

    scheduler = Scheduler()
    # Task is "overdue" (due yesterday) to exercise the today-anchored logic
    yesterday = datetime.now() - timedelta(days=1)
    task = _make_task(
        task_id=10, pet_id=1,
        due_time=yesterday,
        recurring=True, recurrence_pattern="daily",
    )
    scheduler.add_task(task)

    next_task = scheduler.complete_task(task_id=10)

    assert next_task is not None, "No next occurrence was created"
    assert next_task._due_time.date() == date.today() + timedelta(days=1), (
        "Next occurrence should be tomorrow, not today or another date"
    )


def test_daily_recurrence_preserves_time_of_day():
    """The generated next occurrence must keep the original task's time-of-day."""
    from pawpal_system import Scheduler

    scheduler = Scheduler()
    due = datetime(2026, 3, 29, 8, 30)   # 08:30 yesterday (relative to test date)
    task = _make_task(
        task_id=11, pet_id=1,
        due_time=due,
        recurring=True, recurrence_pattern="daily",
    )
    scheduler.add_task(task)

    next_task = scheduler.complete_task(task_id=11)

    assert next_task._due_time.hour == 8
    assert next_task._due_time.minute == 30


def test_completing_daily_task_marks_original_complete():
    """complete_task() must flip the original task's status to 'complete'."""
    from pawpal_system import Scheduler
    from datetime import timedelta

    scheduler = Scheduler()
    task = _make_task(
        task_id=12, pet_id=1,
        due_time=datetime.now() - timedelta(days=1),
        recurring=True, recurrence_pattern="daily",
    )
    scheduler.add_task(task)
    scheduler.complete_task(task_id=12)

    assert task._status == "complete"


def test_non_recurring_task_produces_no_next_occurrence():
    """Completing a non-recurring task must return None (no new task created)."""
    from pawpal_system import Scheduler

    scheduler = Scheduler()
    task = _make_task(task_id=20, pet_id=1, due_time=datetime(2026, 4, 1, 9, 0))
    scheduler.add_task(task)

    result = scheduler.complete_task(task_id=20)

    assert result is None


def test_monthly_recurring_task_produces_no_auto_occurrence():
    """Monthly tasks must NOT auto-generate a next occurrence (managed manually)."""
    from pawpal_system import Scheduler

    scheduler = Scheduler()
    task = _make_task(
        task_id=21, pet_id=1,
        due_time=datetime(2026, 4, 1, 9, 0),
        recurring=True, recurrence_pattern="monthly",
    )
    scheduler.add_task(task)

    result = scheduler.complete_task(task_id=21)

    assert result is None


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_flags_same_time_tasks():
    """Two pending tasks for the same pet at the same time must be flagged."""
    from pawpal_system import Scheduler

    scheduler = Scheduler()
    same_time = datetime(2026, 4, 1, 13, 0)
    t1 = _make_task(task_id=30, pet_id=2, due_time=same_time)
    t2 = _make_task(task_id=31, pet_id=2, due_time=same_time)
    scheduler.add_task(t1)
    scheduler.add_task(t2)

    conflicts = scheduler.detect_conflicts(pet_id=2, window_minutes=0)

    assert len(conflicts) >= 1, "Expected at least one conflict for overlapping tasks"


def test_detect_conflicts_no_false_positives_outside_window():
    """Tasks more than window_minutes apart must not be flagged as conflicts."""
    from pawpal_system import Scheduler

    scheduler = Scheduler()
    t1 = _make_task(task_id=32, pet_id=3, due_time=datetime(2026, 4, 1, 9,  0))
    t2 = _make_task(task_id=33, pet_id=3, due_time=datetime(2026, 4, 1, 11, 0))
    scheduler.add_task(t1)
    scheduler.add_task(t2)

    conflicts = scheduler.detect_conflicts(pet_id=3, window_minutes=30)

    assert conflicts == [], "Tasks 2 hours apart should not conflict within a 30-min window"


def test_detect_all_conflicts_catches_cross_pet_overlap():
    """detect_all_conflicts() must catch same-time tasks across different pets."""
    from pawpal_system import Scheduler

    scheduler = Scheduler()
    same_time = datetime(2026, 4, 1, 13, 0)
    t1 = _make_task(task_id=40, pet_id=4, due_time=same_time)
    t2 = _make_task(task_id=41, pet_id=5, due_time=same_time)
    scheduler.add_task(t1)
    scheduler.add_task(t2)

    conflicts = scheduler.detect_all_conflicts(window_minutes=0)

    assert len(conflicts) >= 1, "Cross-pet same-time conflict was not detected"


def test_completed_tasks_excluded_from_conflict_detection():
    """A completed task must not participate in conflict detection."""
    from pawpal_system import Scheduler

    scheduler = Scheduler()
    same_time = datetime(2026, 4, 1, 13, 0)
    t1 = _make_task(task_id=42, pet_id=6, due_time=same_time, status="complete")
    t2 = _make_task(task_id=43, pet_id=6, due_time=same_time)
    scheduler.add_task(t1)
    scheduler.add_task(t2)

    conflicts = scheduler.detect_conflicts(pet_id=6, window_minutes=0)

    assert conflicts == [], "Completed tasks should be ignored in conflict detection"


if __name__ == "__main__":
    test_mark_complete_changes_status()
    print("PASS  test_mark_complete_changes_status")

    test_add_task_increases_pet_task_count()
    print("PASS  test_add_task_increases_pet_task_count")

    test_sort_by_time_returns_chronological_order()
    print("PASS  test_sort_by_time_returns_chronological_order")

    test_sort_by_time_empty_list()
    print("PASS  test_sort_by_time_empty_list")

    test_sort_by_time_preserves_all_tasks()
    print("PASS  test_sort_by_time_preserves_all_tasks")

    test_daily_recurring_task_creates_next_day_occurrence()
    print("PASS  test_daily_recurring_task_creates_next_day_occurrence")

    test_daily_recurrence_preserves_time_of_day()
    print("PASS  test_daily_recurrence_preserves_time_of_day")

    test_completing_daily_task_marks_original_complete()
    print("PASS  test_completing_daily_task_marks_original_complete")

    test_non_recurring_task_produces_no_next_occurrence()
    print("PASS  test_non_recurring_task_produces_no_next_occurrence")

    test_monthly_recurring_task_produces_no_auto_occurrence()
    print("PASS  test_monthly_recurring_task_produces_no_auto_occurrence")

    test_detect_conflicts_flags_same_time_tasks()
    print("PASS  test_detect_conflicts_flags_same_time_tasks")

    test_detect_conflicts_no_false_positives_outside_window()
    print("PASS  test_detect_conflicts_no_false_positives_outside_window")

    test_detect_all_conflicts_catches_cross_pet_overlap()
    print("PASS  test_detect_all_conflicts_catches_cross_pet_overlap")

    test_completed_tasks_excluded_from_conflict_detection()
    print("PASS  test_completed_tasks_excluded_from_conflict_detection")
