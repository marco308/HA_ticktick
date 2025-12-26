"""Services for TickTick integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import TickTickDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Service names
SERVICE_CREATE_TASK = "create_task"
SERVICE_COMPLETE_TASK = "complete_task"
SERVICE_DELETE_TASK = "delete_task"
SERVICE_UPDATE_TASK = "update_task"
SERVICE_CREATE_SUBTASK = "create_subtask"

# Service schemas
SERVICE_CREATE_TASK_SCHEMA = vol.Schema(
    {
        vol.Required("title"): cv.string,
        vol.Optional("project_id"): cv.string,
        vol.Optional("content"): cv.string,
        vol.Optional("due_date"): cv.string,
        vol.Optional("priority"): vol.In(["none", "low", "medium", "high"]),
        vol.Optional("all_day", default=False): cv.boolean,
    }
)

SERVICE_COMPLETE_TASK_SCHEMA = vol.Schema(
    {
        vol.Required("task_id"): cv.string,
        vol.Required("project_id"): cv.string,
    }
)

SERVICE_DELETE_TASK_SCHEMA = vol.Schema(
    {
        vol.Required("task_id"): cv.string,
        vol.Required("project_id"): cv.string,
    }
)

SERVICE_UPDATE_TASK_SCHEMA = vol.Schema(
    {
        vol.Required("task_id"): cv.string,
        vol.Required("project_id"): cv.string,
        vol.Optional("title"): cv.string,
        vol.Optional("content"): cv.string,
        vol.Optional("due_date"): cv.string,
        vol.Optional("priority"): vol.In(["none", "low", "medium", "high"]),
    }
)

SERVICE_CREATE_SUBTASK_SCHEMA = vol.Schema(
    {
        vol.Required("parent_task_id"): cv.string,
        vol.Required("project_id"): cv.string,
        vol.Required("title"): cv.string,
        vol.Optional("content"): cv.string,
    }
)

PRIORITY_TO_INT = {
    "none": 0,
    "low": 1,
    "medium": 3,
    "high": 5,
}


def _get_coordinator(hass: HomeAssistant) -> TickTickDataUpdateCoordinator | None:
    """Get the coordinator from hass data."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if hasattr(entry, "runtime_data") and entry.runtime_data:
            return entry.runtime_data
    return None


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up TickTick services."""

    async def handle_create_task(call: ServiceCall) -> None:
        """Handle the create task service call."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            _LOGGER.error("TickTick integration not set up")
            return

        title = call.data["title"]
        project_id = call.data.get("project_id")
        content = call.data.get("content")
        due_date = call.data.get("due_date")
        priority_str = call.data.get("priority", "none")
        all_day = call.data.get("all_day", False)

        priority = PRIORITY_TO_INT.get(priority_str, 0)

        # If no project_id specified, try to use the first project (Inbox)
        if not project_id and coordinator.data:
            # Try to find Inbox or use first project
            for proj in coordinator.data.projects.values():
                if proj.name.lower() == "inbox":
                    project_id = proj.id
                    break
            if not project_id:
                projects = list(coordinator.data.projects.values())
                if projects:
                    project_id = projects[0].id

        if not project_id:
            _LOGGER.error("No project specified and no default project found")
            return

        try:
            await coordinator.api.create_task(
                title=title,
                project_id=project_id,
                content=content,
                due_date=due_date,
                priority=priority,
                all_day=all_day,
            )
            await coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to create task: %s", err)

    async def handle_complete_task(call: ServiceCall) -> None:
        """Handle the complete task service call."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            _LOGGER.error("TickTick integration not set up")
            return

        task_id = call.data["task_id"]
        project_id = call.data["project_id"]

        try:
            await coordinator.api.complete_task(project_id, task_id)
            await coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to complete task: %s", err)

    async def handle_delete_task(call: ServiceCall) -> None:
        """Handle the delete task service call."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            _LOGGER.error("TickTick integration not set up")
            return

        task_id = call.data["task_id"]
        project_id = call.data["project_id"]

        try:
            await coordinator.api.delete_task(project_id, task_id)
            await coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to delete task: %s", err)

    async def handle_update_task(call: ServiceCall) -> None:
        """Handle the update task service call."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            _LOGGER.error("TickTick integration not set up")
            return

        task_id = call.data["task_id"]
        project_id = call.data["project_id"]
        title = call.data.get("title")
        content = call.data.get("content")
        due_date = call.data.get("due_date")
        priority_str = call.data.get("priority")

        priority = PRIORITY_TO_INT.get(priority_str) if priority_str else None

        try:
            await coordinator.api.update_task(
                task_id=task_id,
                project_id=project_id,
                title=title,
                content=content,
                due_date=due_date,
                priority=priority,
            )
            await coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to update task: %s", err)

    async def handle_create_subtask(call: ServiceCall) -> None:
        """Handle the create subtask service call."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            _LOGGER.error("TickTick integration not set up")
            return

        parent_task_id = call.data["parent_task_id"]
        project_id = call.data["project_id"]
        title = call.data["title"]
        content = call.data.get("content")

        try:
            await coordinator.api.create_subtask(
                parent_task_id=parent_task_id,
                project_id=project_id,
                title=title,
                content=content,
            )
            await coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to create subtask: %s", err)

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_TASK,
        handle_create_task,
        schema=SERVICE_CREATE_TASK_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_COMPLETE_TASK,
        handle_complete_task,
        schema=SERVICE_COMPLETE_TASK_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_TASK,
        handle_delete_task,
        schema=SERVICE_DELETE_TASK_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_TASK,
        handle_update_task,
        schema=SERVICE_UPDATE_TASK_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_SUBTASK,
        handle_create_subtask,
        schema=SERVICE_CREATE_SUBTASK_SCHEMA,
    )
