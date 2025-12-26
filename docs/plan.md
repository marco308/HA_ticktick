# Home Assistant TickTick Integration Plan

This document outlines the plan for integrating TickTick, a popular task management application, with Home Assistant. The integration will allow users to manage their TickTick tasks directly from Home Assistant, enabling automation and enhanced task management capabilities.

## References

- [Home Assistant Integration Developer Documentation](https://developers.home-assistant.io/docs/creating_component_index/)
- [TickTick API Documentation](https://developer.ticktick.com/docs#/openapi)
- [Home Assistant Calendar Entity](https://developers.home-assistant.io/docs/core/entity/calendar/)

---

## 1. Overview

### Goals
- Provide full TickTick task management within Home Assistant
- Enable automations based on task events
- Display tasks in the HA calendar view
- Support configurable sync intervals

### Integration Type
- **Custom Component**: Installable via HACS or manual installation
- **Config Flow**: User-friendly setup via UI
- **OAuth2 Authentication**: Secure authorization via TickTick login
- **Polling Coordinator**: Configurable sync interval for data updates

---

## 2. Authentication

### OAuth2 Flow
1. User initiates setup via Home Assistant UI
2. Redirect to TickTick authorization page
3. User grants permissions
4. TickTick returns authorization code
5. Integration exchanges code for access/refresh tokens
6. Tokens stored securely in HA config entry

### Required Scopes
- `tasks:read` - Read tasks and projects
- `tasks:write` - Create, update, delete tasks

### Token Management
- Store refresh token in config entry
- Auto-refresh access token before expiration
- Handle token revocation gracefully

---

## 3. Entities

### 3.1 Project Sensors
Each TickTick project becomes a sensor entity.

**Entity ID Format**: `sensor.ticktick_<project_name>`

**State**: Total task count in the project

**Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| `project_id` | string | TickTick project ID |
| `project_name` | string | Project display name |
| `task_count` | int | Total tasks |
| `overdue_count` | int | Overdue tasks |
| `due_today_count` | int | Tasks due today |
| `completed_today` | int | Tasks completed today |
| `tasks` | list | List of task objects with details |

**Device Class**: None (custom)

**Icon**: `mdi:checkbox-marked-circle-outline`

### 3.2 Calendar Entity
A calendar entity to display tasks with due dates.

**Entity ID**: `calendar.ticktick_tasks`

**Features**:
- Tasks with due dates appear as calendar events
- Tasks with specific times show at that time
- Tasks without times show as all-day events
- Color coding by priority (if supported by HA frontend)

---

## 4. Services

### 4.1 Basic Task Operations

#### `ticktick.create_task`
Create a new task in TickTick.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | Yes | Task title |
| `project_id` | string | No | Target project (default: Inbox) |
| `content` | string | No | Task description/notes |
| `due_date` | datetime | No | Due date and time |
| `priority` | string | No | none, low, medium, high |
| `all_day` | bool | No | All-day task (default: false) |

#### `ticktick.complete_task`
Mark a task as complete.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string | Yes | Task to complete |
| `project_id` | string | Yes | Project containing the task |

#### `ticktick.delete_task`
Delete a task.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string | Yes | Task to delete |
| `project_id` | string | Yes | Project containing the task |

### 4.2 Advanced Task Operations

#### `ticktick.update_task`
Update an existing task.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string | Yes | Task to update |
| `project_id` | string | Yes | Project containing the task |
| `title` | string | No | New title |
| `content` | string | No | New description |
| `due_date` | datetime | No | New due date |
| `priority` | string | No | New priority level |

### 4.3 Subtask Operations

#### `ticktick.create_subtask`
Create a subtask under a parent task.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `parent_task_id` | string | Yes | Parent task ID |
| `project_id` | string | Yes | Project ID |
| `title` | string | Yes | Subtask title |

#### `ticktick.complete_subtask`
Mark a subtask as complete.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | string | Yes | Subtask ID |
| `parent_task_id` | string | Yes | Parent task ID |
| `project_id` | string | Yes | Project ID |

---

## 5. Events (Automation Triggers)

The integration fires events that can be used in automations.

### 5.1 `ticktick_task_created`
Fired when a new task is detected.

**Event Data**:
```yaml
task_id: "abc123"
project_id: "proj456"
title: "Buy groceries"
due_date: "2025-01-15T10:00:00"
priority: "medium"
```

### 5.2 `ticktick_task_completed`
Fired when a task is marked complete.

**Event Data**:
```yaml
task_id: "abc123"
project_id: "proj456"
title: "Buy groceries"
completed_at: "2025-01-14T15:30:00"
```

### 5.3 `ticktick_task_due_soon`
Fired when a task is approaching its due date.

**Event Data**:
```yaml
task_id: "abc123"
project_id: "proj456"
title: "Submit report"
due_date: "2025-01-14T17:00:00"
minutes_until_due: 30
```

**Configuration**: Users can set the "due soon" threshold (default: 30 minutes)

---

## 6. Configuration

### Config Flow Steps
1. **Init**: Welcome screen, start OAuth2 flow
2. **OAuth2**: Redirect to TickTick, handle callback
3. **Options**: Configure sync interval and preferences

### User Options
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `scan_interval` | int | 300 | Sync interval in seconds (60-3600) |
| `due_soon_minutes` | int | 30 | Minutes before due to trigger "due soon" event |
| `include_completed` | bool | false | Include recently completed tasks |

---

## 7. File Structure

```
├── hacs.json                 # HACS metadata
├── custom_components/
│   └── ticktick/
│       ├── __init__.py       # Integration setup, coordinator
│       ├── manifest.json     # Integration metadata
│       ├── config_flow.py    # OAuth2 config flow
│       ├── const.py          # Constants and defaults
│       ├── coordinator.py    # Data update coordinator
│       ├── sensor.py         # Project sensor entities
│       ├── calendar.py       # Calendar entity
│       ├── services.py       # Service definitions
│       ├── services.yaml     # Service descriptions
│       ├── api.py            # TickTick API client
│       ├── strings.json      # UI strings
│       └── translations/
│           └── en.json       # English translations
└── README.md                 # Repository documentation
```

---

## 8. Implementation Phases

### Phase 1: Foundation
- [ ] Set up integration structure and manifest
- [ ] Implement OAuth2 authentication flow
- [ ] Create TickTick API client wrapper
- [ ] Implement data update coordinator

### Phase 2: Core Entities
- [ ] Implement project sensors
- [ ] Add sensor attributes (task counts, overdue, etc.)
- [ ] Create calendar entity with task events

### Phase 3: Services
- [ ] Implement basic CRUD services (create, complete, delete)
- [ ] Add advanced update service
- [ ] Implement subtask services

### Phase 4: Automations
- [ ] Fire events for task created/completed
- [ ] Implement "due soon" event logic
- [ ] Add configurable thresholds

### Phase 5: Polish
- [ ] Add user options flow
- [ ] Write tests
- [ ] Documentation and README
- [ ] Error handling and edge cases

---

## 9. API Considerations

### Rate Limits
- TickTick API has rate limits (exact limits TBD from docs)
- Implement exponential backoff on 429 responses
- Respect configurable minimum sync interval

### Data Caching
- Cache project list and task data
- Use ETag/Last-Modified headers if available
- Partial sync for efficiency when possible

### Error Handling
- Handle network timeouts gracefully
- Log API errors with context
- Retry transient failures
- Notify user of persistent auth issues

---

## 10. Example Automations

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

### Turn on office light when work tasks exist
```yaml
automation:
  - alias: "Work Tasks Indicator"
    trigger:
      - platform: state
        entity_id: sensor.ticktick_work
    condition:
      - condition: numeric_state
        entity_id: sensor.ticktick_work
        above: 0
    action:
      - service: light.turn_on
        target:
          entity_id: light.office_indicator
        data:
          color_name: "yellow"
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

---

## 11. Open Questions

1. **Webhook Support**: Does TickTick support webhooks for real-time updates? (Would reduce polling needs)
2. **Batch Operations**: Does the API support batch task operations for efficiency?
3. **Recurring Tasks**: How should recurring tasks be handled in the calendar view?
4. **Shared Projects**: How to handle projects shared with other users?

---

## Next Steps

1. Review this plan and confirm requirements
2. Add TickTick OAuth2 credentials (client ID/secret) to const.py
3. Begin Phase 1 implementation
4. Set up HACS repository structure for distribution
