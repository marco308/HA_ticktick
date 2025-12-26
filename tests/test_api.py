"""Tests for TickTick API client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.ticktick.api import (
    TickTickApi,
    TickTickApiError,
    TickTickAuthError,
)


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock aiohttp session."""
    return MagicMock(spec=aiohttp.ClientSession)


@pytest.fixture
def api(mock_session: MagicMock) -> TickTickApi:
    """Create a TickTick API client with mock session."""
    return TickTickApi(mock_session, "test_access_token")


class TestTickTickApi:
    """Tests for TickTickApi class."""

    def test_headers(self, api: TickTickApi) -> None:
        """Test that headers include authorization."""
        headers = api._headers
        assert headers["Authorization"] == "Bearer test_access_token"
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_get_projects(
        self, api: TickTickApi, mock_session: MagicMock
    ) -> None:
        """Test getting projects."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[{"id": "proj1", "name": "Inbox"}])

        mock_session.request = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        )

        projects = await api.get_projects()
        assert len(projects) == 1
        assert projects[0]["id"] == "proj1"

    @pytest.mark.asyncio
    async def test_auth_error(self, api: TickTickApi, mock_session: MagicMock) -> None:
        """Test that 401 raises TickTickAuthError."""
        mock_response = AsyncMock()
        mock_response.status = 401

        mock_session.request = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        )

        with pytest.raises(TickTickAuthError):
            await api.get_projects()

    @pytest.mark.asyncio
    async def test_rate_limit_error(
        self, api: TickTickApi, mock_session: MagicMock
    ) -> None:
        """Test that 429 raises TickTickApiError."""
        mock_response = AsyncMock()
        mock_response.status = 429

        mock_session.request = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        )

        with pytest.raises(TickTickApiError, match="Rate limit exceeded"):
            await api.get_projects()

    @pytest.mark.asyncio
    async def test_api_error(self, api: TickTickApi, mock_session: MagicMock) -> None:
        """Test that other 4xx/5xx raises TickTickApiError."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")

        mock_session.request = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        )

        with pytest.raises(TickTickApiError, match="API error 500"):
            await api.get_projects()

    @pytest.mark.asyncio
    async def test_create_task(self, api: TickTickApi, mock_session: MagicMock) -> None:
        """Test creating a task."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"id": "new_task", "title": "Test Task"}
        )

        mock_session.request = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        )

        result = await api.create_task(
            title="Test Task",
            project_id="proj1",
            content="Test content",
            due_date="2025-01-15T10:00:00",
            priority=3,
            all_day=False,
        )

        assert result["id"] == "new_task"
        mock_session.request.assert_called_once()
        call_kwargs = mock_session.request.call_args
        assert call_kwargs[0][0] == "POST"

    @pytest.mark.asyncio
    async def test_complete_task(
        self, api: TickTickApi, mock_session: MagicMock
    ) -> None:
        """Test completing a task."""
        mock_response = AsyncMock()
        mock_response.status = 204

        mock_session.request = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        )

        await api.complete_task("proj1", "task1")
        mock_session.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_task(self, api: TickTickApi, mock_session: MagicMock) -> None:
        """Test deleting a task."""
        mock_response = AsyncMock()
        mock_response.status = 204

        mock_session.request = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        )

        await api.delete_task("proj1", "task1")
        mock_session.request.assert_called_once()
        call_args = mock_session.request.call_args[0]
        assert call_args[0] == "DELETE"

    @pytest.mark.asyncio
    async def test_create_subtask(
        self, api: TickTickApi, mock_session: MagicMock
    ) -> None:
        """Test creating a subtask."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"id": "subtask1", "parentId": "task1"}
        )

        mock_session.request = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        )

        result = await api.create_subtask(
            parent_task_id="task1",
            project_id="proj1",
            title="Subtask",
        )

        assert result["id"] == "subtask1"
        assert result["parentId"] == "task1"

    @pytest.mark.asyncio
    async def test_complete_subtask(
        self, api: TickTickApi, mock_session: MagicMock
    ) -> None:
        """Test completing a subtask."""
        mock_response = AsyncMock()
        mock_response.status = 204

        mock_session.request = MagicMock(
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        )

        await api.complete_subtask("proj1", "subtask1")
        mock_session.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_error(
        self, api: TickTickApi, mock_session: MagicMock
    ) -> None:
        """Test that connection errors are wrapped."""
        mock_session.request = MagicMock(
            side_effect=aiohttp.ClientError("Connection failed")
        )

        with pytest.raises(TickTickApiError, match="Connection error"):
            await api.get_projects()
