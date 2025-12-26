# TickTick Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant custom component that integrates with [TickTick](https://ticktick.com), allowing you to view and manage your tasks directly from Home Assistant.

## Features

- **Project Sensors**: Each TickTick project becomes a sensor showing task counts
- **Calendar Integration**: View tasks with due dates in the Home Assistant calendar
- **Task Management Services**: Create, update, complete, and delete tasks via automations
- **Automation Events**: Trigger automations when tasks are created, completed, or due soon
- **OAuth2 Authentication**: Secure login via your TickTick account

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add this repository URL and select **Integration** as the category
4. Click **Install**
5. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/ticktick` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

### Prerequisites

You need TickTick API credentials (OAuth2 client ID and secret):

1. Go to the [TickTick Developer Portal](https://developer.ticktick.com/)
2. Create a new application
3. Set the redirect URI to: `https://my.home-assistant.io/redirect/oauth`
4. Note your **Client ID** and **Client Secret**

### Setup

1. In Home Assistant, go to **Settings** → **Devices & Services** → **Application Credentials**
2. Click **Add Credentials** and select "TickTick"
3. Enter your Client ID and Client Secret from the TickTick Developer Portal
4. Go to **Settings** → **Devices & Services** → **Add Integration**
5. Search for "TickTick" and follow the OAuth2 flow to authorize
6. Configure options (sync interval, due soon threshold)

## Entities

### Project Sensors

Each TickTick project creates a sensor entity:

- **Entity ID**: `sensor.ticktick_<project_name>`
- **State**: Total task count
- **Attributes**:
  - `project_id`: TickTick project ID
  - `project_name`: Project display name
  - `task_count`: Total tasks
  - `overdue_count`: Overdue tasks
  - `due_today_count`: Tasks due today
  - `tasks`: List of task objects

### Calendar

A single calendar entity displays all tasks with due dates:

- **Entity ID**: `calendar.ticktick_tasks`
- Tasks with specific times appear at that time
- Tasks without times appear as all-day events

## Services

### `ticktick.create_task`

Create a new task.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | Yes | Task title |
| `project_id` | string | No | Target project (default: Inbox) |
| `content` | string | No | Task description |
| `due_date` | string | No | Due date (ISO format) |
| `priority` | string | No | `none`, `low`, `medium`, `high` |
| `all_day` | bool | No | All-day task (default: false) |

```yaml
service: ticktick.create_task
data:
  title: "Buy groceries"
  project_id: "abc123"
  due_date: "2025-01-15T10:00:00"
  priority: "medium"
```

### `ticktick.complete_task`

Mark a task as complete.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string | Yes | Task ID |
| `project_id` | string | Yes | Project ID |

### `ticktick.delete_task`

Delete a task.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string | Yes | Task ID |
| `project_id` | string | Yes | Project ID |

### `ticktick.update_task`

Update an existing task.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string | Yes | Task ID |
| `project_id` | string | Yes | Project ID |
| `title` | string | No | New title |
| `content` | string | No | New description |
| `due_date` | string | No | New due date |
| `priority` | string | No | New priority |

### `ticktick.create_subtask`

Create a subtask under a parent task.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `parent_task_id` | string | Yes | Parent task ID |
| `project_id` | string | Yes | Project ID |
| `title` | string | Yes | Subtask title |
| `content` | string | No | Subtask description |

### `ticktick.complete_subtask`

Mark a subtask as complete.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string | Yes | Subtask ID |
| `parent_task_id` | string | Yes | Parent task ID |
| `project_id` | string | Yes | Project ID |

## Events

The integration fires events for use in automations:

### `ticktick_task_created`

Fired when a new task is detected.

```yaml
event_data:
  task_id: "abc123"
  project_id: "proj456"
  title: "Buy groceries"
  due_date: "2025-01-15T10:00:00"
  priority: 3
```

### `ticktick_task_completed`

Fired when a task is marked complete.

```yaml
event_data:
  task_id: "abc123"
  completed_at: "2025-01-14T15:30:00"
```

### `ticktick_task_due_soon`

Fired when a task is approaching its due date (configurable threshold, default 30 minutes).

```yaml
event_data:
  task_id: "abc123"
  project_id: "proj456"
  title: "Submit report"
  due_date: "2025-01-14T17:00:00"
  minutes_until_due: 30
```

## Example Automations

### Notify when task is due soon

```yaml
automation:
  - alias: "TickTick Due Soon Notification"
    trigger:
      - platform: event
        event_type: ticktick_task_due_soon
    action:
      - service: notify.mobile_app
        data:
          title: "Task Due Soon"
          message: "{{ trigger.event.data.title }} is due in {{ trigger.event.data.minutes_until_due }} minutes"
```

### Create task via voice assistant

```yaml
script:
  add_shopping_item:
    alias: "Add Shopping Item"
    sequence:
      - service: ticktick.create_task
        data:
          title: "{{ item }}"
          project_id: "shopping_list_project_id"
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `scan_interval` | 300 | Sync interval in seconds (60-3600) |
| `due_soon_minutes` | 30 | Minutes before due to trigger event |
| `include_completed` | false | Include recently completed tasks |

## Development

### Setup

```bash
poetry install
```

### Running Tests

```bash
pytest
```

### Running Tests with Coverage

```bash
pytest --cov --cov-report=html
```

### Linting

```bash
ruff check .
ruff format .
```

### Type Checking

```bash
mypy custom_components/ticktick
```

## License

This project is licensed under the MIT License.
