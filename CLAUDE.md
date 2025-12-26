# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant custom component that integrates with TickTick task management. It allows users to view and manage their TickTick tasks from within Home Assistant, including automation triggers based on task events.

**Installation**: Via HACS (Home Assistant Community Store) or manual installation to `custom_components/ticktick/`.

## Architecture

### Core Components

- **`api.py`** - TickTick API client using aiohttp. Wraps all REST endpoints (projects, tasks, subtasks). Raises `TickTickApiError` or `TickTickAuthError`.

- **`coordinator.py`** - Data update coordinator (polling pattern). Fetches all projects and tasks, fires events for task changes (`ticktick_task_created`, `ticktick_task_completed`, `ticktick_task_due_soon`). Contains dataclasses: `TickTickProject`, `TickTickTask`, `TickTickData`.

- **`config_flow.py`** - OAuth2 authentication flow using Home Assistant's `config_entry_oauth2_flow`. Handles token storage and refresh.

- **`sensor.py`** - Creates one sensor per TickTick project. State is task count, attributes include overdue/due today counts and full task list.

- **`calendar.py`** - Single calendar entity showing all tasks with due dates as events.

- **`services.py`** - Registers HA services: `create_task`, `complete_task`, `delete_task`, `update_task`, `create_subtask`.

### Data Flow

1. OAuth2 token obtained via config flow, stored in config entry
2. Coordinator polls TickTick API at configurable interval (default 5 min)
3. Coordinator stores `TickTickData` with projects and tasks
4. Entities read from coordinator data
5. Services call API directly, then trigger coordinator refresh

### Key Constants (`const.py`)

- API base: `https://api.ticktick.com/open/v1`
- OAuth2 endpoints: `https://ticktick.com/oauth/authorize`, `https://ticktick.com/oauth/token`
- Priority values: 0=none, 1=low, 3=medium, 5=high

## Setup Requirements

Before the integration works, OAuth2 credentials must be configured in `const.py`:
```python
CLIENT_ID: Final = "YOUR_CLIENT_ID"
CLIENT_SECRET: Final = "YOUR_CLIENT_SECRET"
```

These are obtained from the TickTick Developer Portal.

## Home Assistant Patterns

This integration follows standard HA custom component patterns:
- Uses `ConfigEntry.runtime_data` for coordinator storage (type alias: `TickTickConfigEntry`)
- Entities extend `CoordinatorEntity` for automatic update handling
- Services defined in `services.yaml` with schemas in `services.py`
- Translations in `translations/en.json`, strings in `strings.json`
