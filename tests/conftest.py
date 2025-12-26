"""Fixtures for TickTick integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ticktick.api import TickTickApi
from custom_components.ticktick.coordinator import (
    TickTickData,
    TickTickProject,
    TickTickTask,
)


@pytest.fixture
def mock_api() -> Generator[AsyncMock, None, None]:
    """Create a mock TickTick API client."""
    with patch(
        "custom_components.ticktick.api.TickTickApi", autospec=True
    ) as mock_api_class:
        api = mock_api_class.return_value
        api.get_projects = AsyncMock(return_value=[])
        api.get_project_with_tasks = AsyncMock(return_value={"tasks": []})
        api.create_task = AsyncMock(return_value={"id": "new_task_id"})
        api.update_task = AsyncMock(return_value={"id": "task_id"})
        api.complete_task = AsyncMock(return_value=None)
        api.delete_task = AsyncMock(return_value=None)
        api.create_subtask = AsyncMock(return_value={"id": "new_subtask_id"})
        api.complete_subtask = AsyncMock(return_value=None)
        api.get_user_info = AsyncMock(return_value={"project_count": 1})
        yield api


@pytest.fixture
def sample_projects() -> list[dict]:
    """Return sample project data from API."""
    return [
        {
            "id": "proj1",
            "name": "Inbox",
            "color": "#FF0000",
        },
        {
            "id": "proj2",
            "name": "Work",
            "color": "#00FF00",
        },
    ]


@pytest.fixture
def sample_tasks() -> list[dict]:
    """Return sample task data from API."""
    return [
        {
            "id": "task1",
            "projectId": "proj1",
            "title": "Buy groceries",
            "content": "Milk, eggs, bread",
            "dueDate": "2025-01-15T10:00:00+00:00",
            "priority": 3,
            "isAllDay": False,
            "status": 0,
        },
        {
            "id": "task2",
            "projectId": "proj1",
            "title": "Call mom",
            "content": None,
            "dueDate": None,
            "priority": 0,
            "isAllDay": False,
            "status": 0,
        },
        {
            "id": "task3",
            "projectId": "proj2",
            "title": "Finish report",
            "content": "Q4 summary",
            "dueDate": "2025-01-20T17:00:00+00:00",
            "priority": 5,
            "isAllDay": False,
            "status": 0,
        },
    ]


@pytest.fixture
def sample_ticktick_data(sample_projects, sample_tasks) -> TickTickData:
    """Return sample TickTickData object."""
    tasks_by_id = {}
    projects = {}

    for proj_data in sample_projects:
        proj_tasks = []
        for task_data in sample_tasks:
            if task_data["projectId"] == proj_data["id"]:
                task = TickTickTask.from_api(task_data)
                proj_tasks.append(task)
                tasks_by_id[task.id] = task

        projects[proj_data["id"]] = TickTickProject(
            id=proj_data["id"],
            name=proj_data["name"],
            color=proj_data.get("color"),
            tasks=proj_tasks,
        )

    return TickTickData(projects=projects, tasks=tasks_by_id)
