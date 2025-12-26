"""Tests for TickTick data coordinator."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from custom_components.ticktick.coordinator import (
    TickTickData,
    TickTickProject,
    TickTickTask,
)


class TestTickTickTask:
    """Tests for TickTickTask dataclass."""

    def test_from_api_full_data(self) -> None:
        """Test creating task from complete API data."""
        data = {
            "id": "task1",
            "projectId": "proj1",
            "title": "Test Task",
            "content": "Task content",
            "dueDate": "2025-01-15T10:00:00+00:00",
            "priority": 5,
            "isAllDay": False,
            "status": 0,
            "parentId": "parent1",
        }

        task = TickTickTask.from_api(data)

        assert task.id == "task1"
        assert task.project_id == "proj1"
        assert task.title == "Test Task"
        assert task.content == "Task content"
        assert task.due_date is not None
        assert task.priority == 5
        assert task.is_all_day is False
        assert task.status == 0
        assert task.parent_id == "parent1"

    def test_from_api_minimal_data(self) -> None:
        """Test creating task from minimal API data."""
        data = {
            "id": "task1",
            "projectId": "proj1",
        }

        task = TickTickTask.from_api(data)

        assert task.id == "task1"
        assert task.project_id == "proj1"
        assert task.title == ""
        assert task.content is None
        assert task.due_date is None
        assert task.priority == 0
        assert task.is_all_day is False
        assert task.status == 0
        assert task.parent_id is None

    def test_from_api_invalid_date(self) -> None:
        """Test that invalid dates are handled gracefully."""
        data = {
            "id": "task1",
            "projectId": "proj1",
            "dueDate": "invalid-date",
        }

        task = TickTickTask.from_api(data)
        assert task.due_date is None

    def test_from_api_zulu_time(self) -> None:
        """Test parsing date with Z suffix."""
        data = {
            "id": "task1",
            "projectId": "proj1",
            "dueDate": "2025-01-15T10:00:00Z",
        }

        task = TickTickTask.from_api(data)
        assert task.due_date is not None
        assert task.due_date.hour == 10


class TestTickTickProject:
    """Tests for TickTickProject dataclass."""

    def test_task_count(self) -> None:
        """Test task count property."""
        tasks = [
            TickTickTask(
                id=f"task{i}",
                project_id="proj1",
                title=f"Task {i}",
                content=None,
                due_date=None,
                priority=0,
                is_all_day=False,
                status=0,
            )
            for i in range(5)
        ]

        project = TickTickProject(
            id="proj1",
            name="Test Project",
            color="#FF0000",
            tasks=tasks,
        )

        assert project.task_count == 5

    def test_overdue_count(self) -> None:
        """Test overdue count property."""
        now = datetime.now(tz=UTC)
        tasks = [
            TickTickTask(
                id="task1",
                project_id="proj1",
                title="Overdue",
                content=None,
                due_date=now - timedelta(days=1),
                priority=0,
                is_all_day=False,
                status=0,
            ),
            TickTickTask(
                id="task2",
                project_id="proj1",
                title="Future",
                content=None,
                due_date=now + timedelta(days=1),
                priority=0,
                is_all_day=False,
                status=0,
            ),
            TickTickTask(
                id="task3",
                project_id="proj1",
                title="No due date",
                content=None,
                due_date=None,
                priority=0,
                is_all_day=False,
                status=0,
            ),
        ]

        project = TickTickProject(
            id="proj1",
            name="Test Project",
            color=None,
            tasks=tasks,
        )

        assert project.overdue_count == 1

    def test_due_today_count(self) -> None:
        """Test due today count property."""
        now = datetime.now(tz=UTC)
        tasks = [
            TickTickTask(
                id="task1",
                project_id="proj1",
                title="Due today",
                content=None,
                due_date=now.replace(hour=23, minute=59),
                priority=0,
                is_all_day=False,
                status=0,
            ),
            TickTickTask(
                id="task2",
                project_id="proj1",
                title="Due tomorrow",
                content=None,
                due_date=now + timedelta(days=1),
                priority=0,
                is_all_day=False,
                status=0,
            ),
        ]

        project = TickTickProject(
            id="proj1",
            name="Test Project",
            color=None,
            tasks=tasks,
        )

        assert project.due_today_count == 1


class TestTickTickData:
    """Tests for TickTickData dataclass."""

    def test_empty_data(self) -> None:
        """Test empty data structure."""
        data = TickTickData(projects={}, tasks={})
        assert len(data.projects) == 0
        assert len(data.tasks) == 0

    def test_with_projects_and_tasks(self, sample_ticktick_data) -> None:
        """Test data with projects and tasks."""
        assert len(sample_ticktick_data.projects) == 2
        assert len(sample_ticktick_data.tasks) == 3
        assert "proj1" in sample_ticktick_data.projects
        assert "task1" in sample_ticktick_data.tasks
