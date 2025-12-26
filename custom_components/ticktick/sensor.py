"""Sensor platform for TickTick integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TickTickConfigEntry
from .const import DOMAIN, PRIORITY_MAP
from .coordinator import TickTickDataUpdateCoordinator, TickTickProject

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: TickTickConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TickTick sensors from a config entry."""
    coordinator = entry.runtime_data

    # Create a sensor for each project
    entities: list[TickTickProjectSensor] = []

    if coordinator.data:
        for project in coordinator.data.projects.values():
            entities.append(TickTickProjectSensor(coordinator, project.id))

    async_add_entities(entities)

    # Set up listener for new projects
    @callback
    def async_check_new_projects() -> None:
        """Check for new projects and add sensors."""
        if not coordinator.data:
            return

        current_project_ids = {
            entity.project_id
            for entity in entities
            if isinstance(entity, TickTickProjectSensor)
        }

        new_entities = []
        for project_id in coordinator.data.projects:
            if project_id not in current_project_ids:
                new_entity = TickTickProjectSensor(coordinator, project_id)
                entities.append(new_entity)
                new_entities.append(new_entity)

        if new_entities:
            async_add_entities(new_entities)

    entry.async_on_unload(
        coordinator.async_add_listener(async_check_new_projects)
    )


class TickTickProjectSensor(
    CoordinatorEntity[TickTickDataUpdateCoordinator], SensorEntity
):
    """Representation of a TickTick project sensor."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:checkbox-marked-circle-outline"

    def __init__(
        self,
        coordinator: TickTickDataUpdateCoordinator,
        project_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.project_id = project_id
        self._attr_unique_id = f"{DOMAIN}_{project_id}"

    @property
    def _project(self) -> TickTickProject | None:
        """Return the project data."""
        if self.coordinator.data:
            return self.coordinator.data.projects.get(self.project_id)
        return None

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        if self._project:
            return self._project.name
        return "Unknown Project"

    @property
    def native_value(self) -> int:
        """Return the state of the sensor (task count)."""
        if self._project:
            return self._project.task_count
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self._project:
            return {}

        # Build task list with details
        tasks_list = []
        for task in self._project.tasks:
            tasks_list.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "priority": PRIORITY_MAP.get(task.priority, "none"),
                    "is_all_day": task.is_all_day,
                }
            )

        return {
            "project_id": self._project.id,
            "project_name": self._project.name,
            "task_count": self._project.task_count,
            "overdue_count": self._project.overdue_count,
            "due_today_count": self._project.due_today_count,
            "color": self._project.color,
            "tasks": tasks_list,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self._project is not None
