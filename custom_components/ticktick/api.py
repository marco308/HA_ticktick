"""TickTick API Client."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)


class TickTickApiError(Exception):
    """Base exception for TickTick API errors."""


class TickTickAuthError(TickTickApiError):
    """Authentication error."""


class TickTickApi:
    """TickTick API client."""

    def __init__(self, session: aiohttp.ClientSession, access_token: str) -> None:
        """Initialize the API client."""
        self._session = session
        self._access_token = access_token

    @property
    def _headers(self) -> dict[str, str]:
        """Return request headers."""
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> Any:
        """Make an API request."""
        url = f"{API_BASE_URL}{endpoint}"

        try:
            async with self._session.request(
                method,
                url,
                headers=self._headers,
                json=data,
            ) as response:
                if response.status == 401:
                    raise TickTickAuthError("Invalid or expired access token")
                if response.status == 429:
                    raise TickTickApiError("Rate limit exceeded")
                if response.status >= 400:
                    text = await response.text()
                    raise TickTickApiError(f"API error {response.status}: {text}")

                if response.status == 204:
                    return None

                return await response.json()

        except aiohttp.ClientError as err:
            raise TickTickApiError(f"Connection error: {err}") from err

    # Project endpoints
    async def get_projects(self) -> list[dict[str, Any]]:
        """Get all projects."""
        return await self._request("GET", "/project")

    async def get_project(self, project_id: str) -> dict[str, Any]:
        """Get a specific project."""
        return await self._request("GET", f"/project/{project_id}")

    async def get_project_with_tasks(self, project_id: str) -> dict[str, Any]:
        """Get a project with all its tasks."""
        return await self._request("GET", f"/project/{project_id}/data")

    # Task endpoints
    async def get_task(self, project_id: str, task_id: str) -> dict[str, Any]:
        """Get a specific task."""
        return await self._request("GET", f"/project/{project_id}/task/{task_id}")

    async def create_task(
        self,
        title: str,
        project_id: str,
        content: str | None = None,
        due_date: str | None = None,
        priority: int = 0,
        all_day: bool = False,
    ) -> dict[str, Any]:
        """Create a new task."""
        data: dict[str, Any] = {
            "title": title,
            "projectId": project_id,
            "priority": priority,
        }

        if content:
            data["content"] = content
        if due_date:
            data["dueDate"] = due_date
            data["isAllDay"] = all_day

        return await self._request("POST", "/task", data)

    async def update_task(
        self,
        task_id: str,
        project_id: str,
        title: str | None = None,
        content: str | None = None,
        due_date: str | None = None,
        priority: int | None = None,
    ) -> dict[str, Any]:
        """Update an existing task."""
        data: dict[str, Any] = {
            "id": task_id,
            "projectId": project_id,
        }

        if title is not None:
            data["title"] = title
        if content is not None:
            data["content"] = content
        if due_date is not None:
            data["dueDate"] = due_date
        if priority is not None:
            data["priority"] = priority

        return await self._request("POST", f"/task/{task_id}", data)

    async def complete_task(self, project_id: str, task_id: str) -> None:
        """Mark a task as complete."""
        await self._request("POST", f"/project/{project_id}/task/{task_id}/complete")

    async def delete_task(self, project_id: str, task_id: str) -> None:
        """Delete a task."""
        await self._request("DELETE", f"/project/{project_id}/task/{task_id}")

    # Subtask operations
    async def create_subtask(
        self,
        parent_task_id: str,
        project_id: str,
        title: str,
        content: str | None = None,
    ) -> dict[str, Any]:
        """Create a subtask under a parent task."""
        data: dict[str, Any] = {
            "title": title,
            "projectId": project_id,
            "parentId": parent_task_id,
        }

        if content:
            data["content"] = content

        return await self._request("POST", "/task", data)

    # User info (for testing auth)
    async def get_user_info(self) -> dict[str, Any]:
        """Get current user info to validate authentication."""
        # Try getting projects as a way to validate the token
        projects = await self.get_projects()
        return {"project_count": len(projects)}
