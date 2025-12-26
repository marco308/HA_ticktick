"""Tests for TickTick services."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol

from custom_components.ticktick.services import (
    PRIORITY_TO_INT,
    SERVICE_COMPLETE_SUBTASK_SCHEMA,
    SERVICE_COMPLETE_TASK_SCHEMA,
    SERVICE_CREATE_SUBTASK_SCHEMA,
    SERVICE_CREATE_TASK_SCHEMA,
    SERVICE_DELETE_TASK_SCHEMA,
    SERVICE_UPDATE_TASK_SCHEMA,
)


class TestServiceSchemas:
    """Tests for service validation schemas."""

    def test_create_task_schema_valid(self) -> None:
        """Test valid create_task schema."""
        data = {
            "title": "Test Task",
            "project_id": "proj1",
            "content": "Description",
            "due_date": "2025-01-15T10:00:00",
            "priority": "high",
            "all_day": False,
        }
        validated = SERVICE_CREATE_TASK_SCHEMA(data)
        assert validated["title"] == "Test Task"
        assert validated["priority"] == "high"

    def test_create_task_schema_minimal(self) -> None:
        """Test create_task schema with only required fields."""
        data = {"title": "Test Task"}
        validated = SERVICE_CREATE_TASK_SCHEMA(data)
        assert validated["title"] == "Test Task"
        assert validated["all_day"] is False

    def test_create_task_schema_missing_title(self) -> None:
        """Test that missing title raises error."""
        data = {"project_id": "proj1"}
        with pytest.raises(vol.MultipleInvalid):
            SERVICE_CREATE_TASK_SCHEMA(data)

    def test_create_task_schema_invalid_priority(self) -> None:
        """Test that invalid priority raises error."""
        data = {"title": "Test", "priority": "invalid"}
        with pytest.raises(vol.MultipleInvalid):
            SERVICE_CREATE_TASK_SCHEMA(data)

    def test_complete_task_schema_valid(self) -> None:
        """Test valid complete_task schema."""
        data = {"task_id": "task1", "project_id": "proj1"}
        validated = SERVICE_COMPLETE_TASK_SCHEMA(data)
        assert validated["task_id"] == "task1"
        assert validated["project_id"] == "proj1"

    def test_complete_task_schema_missing_fields(self) -> None:
        """Test that missing required fields raise error."""
        with pytest.raises(vol.MultipleInvalid):
            SERVICE_COMPLETE_TASK_SCHEMA({"task_id": "task1"})

        with pytest.raises(vol.MultipleInvalid):
            SERVICE_COMPLETE_TASK_SCHEMA({"project_id": "proj1"})

    def test_delete_task_schema_valid(self) -> None:
        """Test valid delete_task schema."""
        data = {"task_id": "task1", "project_id": "proj1"}
        validated = SERVICE_DELETE_TASK_SCHEMA(data)
        assert validated["task_id"] == "task1"

    def test_update_task_schema_valid(self) -> None:
        """Test valid update_task schema."""
        data = {
            "task_id": "task1",
            "project_id": "proj1",
            "title": "Updated Title",
            "priority": "medium",
        }
        validated = SERVICE_UPDATE_TASK_SCHEMA(data)
        assert validated["title"] == "Updated Title"
        assert validated["priority"] == "medium"

    def test_update_task_schema_required_only(self) -> None:
        """Test update_task with only required fields."""
        data = {"task_id": "task1", "project_id": "proj1"}
        validated = SERVICE_UPDATE_TASK_SCHEMA(data)
        assert "title" not in validated
        assert "content" not in validated

    def test_create_subtask_schema_valid(self) -> None:
        """Test valid create_subtask schema."""
        data = {
            "parent_task_id": "task1",
            "project_id": "proj1",
            "title": "Subtask",
            "content": "Details",
        }
        validated = SERVICE_CREATE_SUBTASK_SCHEMA(data)
        assert validated["parent_task_id"] == "task1"
        assert validated["title"] == "Subtask"

    def test_create_subtask_schema_minimal(self) -> None:
        """Test create_subtask with required fields only."""
        data = {
            "parent_task_id": "task1",
            "project_id": "proj1",
            "title": "Subtask",
        }
        validated = SERVICE_CREATE_SUBTASK_SCHEMA(data)
        assert "content" not in validated

    def test_complete_subtask_schema_valid(self) -> None:
        """Test valid complete_subtask schema."""
        data = {
            "task_id": "subtask1",
            "parent_task_id": "task1",
            "project_id": "proj1",
        }
        validated = SERVICE_COMPLETE_SUBTASK_SCHEMA(data)
        assert validated["task_id"] == "subtask1"
        assert validated["parent_task_id"] == "task1"
        assert validated["project_id"] == "proj1"

    def test_complete_subtask_schema_missing_fields(self) -> None:
        """Test that missing required fields raise error."""
        with pytest.raises(vol.MultipleInvalid):
            SERVICE_COMPLETE_SUBTASK_SCHEMA({"task_id": "subtask1"})


class TestPriorityMapping:
    """Tests for priority string to int mapping."""

    def test_priority_none(self) -> None:
        """Test none priority."""
        assert PRIORITY_TO_INT["none"] == 0

    def test_priority_low(self) -> None:
        """Test low priority."""
        assert PRIORITY_TO_INT["low"] == 1

    def test_priority_medium(self) -> None:
        """Test medium priority."""
        assert PRIORITY_TO_INT["medium"] == 3

    def test_priority_high(self) -> None:
        """Test high priority."""
        assert PRIORITY_TO_INT["high"] == 5

    def test_all_priorities_mapped(self) -> None:
        """Test that all expected priorities are mapped."""
        assert len(PRIORITY_TO_INT) == 4
        assert set(PRIORITY_TO_INT.keys()) == {"none", "low", "medium", "high"}
