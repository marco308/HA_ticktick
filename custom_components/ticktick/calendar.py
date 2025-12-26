"""Calendar platform for TickTick integration."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import TickTickConfigEntry
from .const import DOMAIN, PRIORITY_MAP
from .coordinator import TickTickDataUpdateCoordinator, TickTickTask

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TickTickConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TickTick calendar from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities([TickTickCalendar(coordinator)])


class TickTickCalendar(
    CoordinatorEntity[TickTickDataUpdateCoordinator], CalendarEntity
):
    """Representation of a TickTick calendar."""

    _attr_has_entity_name = True
    _attr_name = "Tasks"

    def __init__(self, coordinator: TickTickDataUpdateCoordinator) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_calendar"

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        now = dt_util.now()
        upcoming_events = self._get_events_in_range(
            now, now + timedelta(days=7)
        )

        if not upcoming_events:
            return None

        # Sort by start time and return the first
        upcoming_events.sort(key=lambda e: e.start)
        return upcoming_events[0]

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        return self._get_events_in_range(start_date, end_date)

    def _get_events_in_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Get calendar events in a date range."""
        events: list[CalendarEvent] = []

        if not self.coordinator.data:
            return events

        # Ensure dates are timezone-aware for comparison
        if start_date.tzinfo is None:
            start_date = dt_util.as_local(start_date)
        if end_date.tzinfo is None:
            end_date = dt_util.as_local(end_date)

        for task in self.coordinator.data.tasks.values():
            if not task.due_date:
                continue

            # Make task due_date timezone-aware if needed
            task_due = task.due_date
            if task_due.tzinfo is None:
                task_due = dt_util.as_local(task_due)

            # Check if task falls within range
            if task.is_all_day:
                # For all-day events, check the date portion
                task_date = task_due.date()
                if start_date.date() <= task_date <= end_date.date():
                    events.append(self._task_to_event(task))
            else:
                # For timed events, check the datetime
                if start_date <= task_due <= end_date:
                    events.append(self._task_to_event(task))

        return events

    def _task_to_event(self, task: TickTickTask) -> CalendarEvent:
        """Convert a task to a calendar event."""
        if not task.due_date:
            raise ValueError("Task must have a due date")

        # Make due_date timezone-aware
        due_date = task.due_date
        if due_date.tzinfo is None:
            due_date = dt_util.as_local(due_date)

        if task.is_all_day:
            # All-day event: use date objects
            return CalendarEvent(
                start=due_date.date(),
                end=due_date.date() + timedelta(days=1),
                summary=task.title,
                description=self._build_description(task),
                uid=task.id,
            )
        else:
            # Timed event: use datetime objects with 1 hour duration
            return CalendarEvent(
                start=due_date,
                end=due_date + timedelta(hours=1),
                summary=task.title,
                description=self._build_description(task),
                uid=task.id,
            )

    def _build_description(self, task: TickTickTask) -> str:
        """Build event description from task details."""
        parts = []

        if task.content:
            parts.append(task.content)

        priority = PRIORITY_MAP.get(task.priority, "none")
        if priority != "none":
            parts.append(f"Priority: {priority.capitalize()}")

        # Get project name
        if self.coordinator.data:
            project = self.coordinator.data.projects.get(task.project_id)
            if project:
                parts.append(f"Project: {project.name}")

        return "\n".join(parts) if parts else ""

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity state attributes."""
        if not self.coordinator.data:
            return {}

        total_tasks = len(self.coordinator.data.tasks)
        tasks_with_due = sum(
            1 for t in self.coordinator.data.tasks.values() if t.due_date
        )

        return {
            "total_tasks": total_tasks,
            "tasks_with_due_date": tasks_with_due,
            "projects_count": len(self.coordinator.data.projects),
        }
