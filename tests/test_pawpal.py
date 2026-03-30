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


if __name__ == "__main__":
    test_mark_complete_changes_status()
    print("PASS  test_mark_complete_changes_status")

    test_add_task_increases_pet_task_count()
    print("PASS  test_add_task_increases_pet_task_count")
