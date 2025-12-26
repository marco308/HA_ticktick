"""Data coordinator for TickTick integration."""

from __future__ import annotations

import contextlib
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TickTickApi, TickTickApiError, TickTickAuthError
from .const import (
    CONF_DUE_SOON_MINUTES,
    CONF_SCAN_INTERVAL,
    DEFAULT_DUE_SOON_MINUTES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EVENT_TASK_COMPLETED,
    EVENT_TASK_CREATED,
    EVENT_TASK_DUE_SOON,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class TickTickProject:
    """Representation of a TickTick project."""

    id: str
    name: str
    color: str | None
    tasks: list[TickTickTask]

    @property
    def task_count(self) -> int:
        """Return total task count."""
        return len(self.tasks)

    @property
    def overdue_count(self) -> int:
        """Return count of overdue tasks."""
        now = datetime.now()
        return sum(
            1 for task in self.tasks if task.due_date and task.due_date < now
        )

    @property
    def due_today_count(self) -> int:
        """Return count of tasks due today."""
        today = datetime.now().date()
        return sum(
            1
            for task in self.tasks
            if task.due_date and task.due_date.date() == today
        )


@dataclass
class TickTickTask:
    """Representation of a TickTick task."""

    id: str
    project_id: str
    title: str
    content: str | None
    due_date: datetime | None
    priority: int
    is_all_day: bool
    status: int
    parent_id: str | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> TickTickTask:
        """Create a task from API data."""
        due_date = None
        if data.get("dueDate"):
            with contextlib.suppress(ValueError, TypeError):
                due_date = datetime.fromisoformat(
                    data["dueDate"].replace("Z", "+00:00")
                )

        return cls(
            id=data["id"],
            project_id=data["projectId"],
            title=data.get("title", ""),
            content=data.get("content"),
            due_date=due_date,
            priority=data.get("priority", 0),
            is_all_day=data.get("isAllDay", False),
            status=data.get("status", 0),
            parent_id=data.get("parentId"),
        )


@dataclass
class TickTickData:
    """Data class for TickTick coordinator."""

    projects: dict[str, TickTickProject]
    tasks: dict[str, TickTickTask]


class TickTickDataUpdateCoordinator(DataUpdateCoordinator[TickTickData]):
    """Class to manage fetching TickTick data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        api: TickTickApi,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        self.api = api
        self._previous_tasks: set[str] = set()
        self._notified_due_soon: set[str] = set()

        scan_interval = config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
            config_entry=config_entry,
        )

    async def _async_update_data(self) -> TickTickData:
        """Fetch data from TickTick API."""
        try:
            # Get all projects
            projects_data = await self.api.get_projects()

            projects: dict[str, TickTickProject] = {}
            all_tasks: dict[str, TickTickTask] = {}
            current_task_ids: set[str] = set()

            for project_data in projects_data:
                project_id = project_data["id"]

                # Get tasks for this project
                try:
                    project_with_tasks = await self.api.get_project_with_tasks(
                        project_id
                    )
                    tasks_data = project_with_tasks.get("tasks", [])
                except TickTickApiError:
                    # If we can't get tasks, continue with empty list
                    tasks_data = []

                tasks = []
                for task_data in tasks_data:
                    # Skip completed tasks (status = 2)
                    if task_data.get("status") == 2:
                        continue

                    task = TickTickTask.from_api(task_data)
                    tasks.append(task)
                    all_tasks[task.id] = task
                    current_task_ids.add(task.id)

                projects[project_id] = TickTickProject(
                    id=project_id,
                    name=project_data.get("name", "Unknown"),
                    color=project_data.get("color"),
                    tasks=tasks,
                )

            # Fire events for new/completed tasks
            await self._fire_task_events(current_task_ids, all_tasks)
            self._previous_tasks = current_task_ids

            # Check for due soon tasks
            await self._check_due_soon(all_tasks)

            return TickTickData(projects=projects, tasks=all_tasks)

        except TickTickAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except TickTickApiError as err:
            raise UpdateFailed(f"Error communicating with TickTick: {err}") from err

    async def _fire_task_events(
        self,
        current_task_ids: set[str],
        tasks: dict[str, TickTickTask],
    ) -> None:
        """Fire events for task changes."""
        # New tasks
        new_task_ids = current_task_ids - self._previous_tasks
        for task_id in new_task_ids:
            if task_id in tasks:
                task = tasks[task_id]
                self.hass.bus.async_fire(
                    EVENT_TASK_CREATED,
                    {
                        "task_id": task.id,
                        "project_id": task.project_id,
                        "title": task.title,
                        "due_date": task.due_date.isoformat() if task.due_date else None,
                        "priority": task.priority,
                    },
                )

        # Completed tasks (were in previous, not in current)
        completed_task_ids = self._previous_tasks - current_task_ids
        for task_id in completed_task_ids:
            # We don't have the task data anymore, just fire with ID
            self.hass.bus.async_fire(
                EVENT_TASK_COMPLETED,
                {
                    "task_id": task_id,
                    "completed_at": datetime.now().isoformat(),
                },
            )

    async def _check_due_soon(self, tasks: dict[str, TickTickTask]) -> None:
        """Check for tasks that are due soon and fire events."""
        due_soon_minutes = self.config_entry.options.get(
            CONF_DUE_SOON_MINUTES, DEFAULT_DUE_SOON_MINUTES
        )
        now = datetime.now()
        threshold = now + timedelta(minutes=due_soon_minutes)

        for task in tasks.values():
            if (
                task.due_date
                and now < task.due_date <= threshold
                and task.id not in self._notified_due_soon
            ):
                minutes_until_due = int(
                    (task.due_date - now).total_seconds() / 60
                )
                self.hass.bus.async_fire(
                    EVENT_TASK_DUE_SOON,
                    {
                        "task_id": task.id,
                        "project_id": task.project_id,
                        "title": task.title,
                        "due_date": task.due_date.isoformat(),
                        "minutes_until_due": minutes_until_due,
                    },
                )
                self._notified_due_soon.add(task.id)

        # Clean up old notifications for tasks that are no longer due soon
        self._notified_due_soon &= set(tasks.keys())
