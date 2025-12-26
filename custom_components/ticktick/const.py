"""Constants for the TickTick integration."""

from typing import Final

DOMAIN: Final = "ticktick"

# OAuth2 Configuration
OAUTH2_AUTHORIZE: Final = "https://ticktick.com/oauth/authorize"
OAUTH2_TOKEN: Final = "https://ticktick.com/oauth/token"

# API Configuration
API_BASE_URL: Final = "https://api.ticktick.com/open/v1"

# Default Configuration
DEFAULT_SCAN_INTERVAL: Final = 300  # 5 minutes
MIN_SCAN_INTERVAL: Final = 60  # 1 minute
MAX_SCAN_INTERVAL: Final = 3600  # 1 hour
DEFAULT_DUE_SOON_MINUTES: Final = 30

# Priority Levels
PRIORITY_NONE: Final = 0
PRIORITY_LOW: Final = 1
PRIORITY_MEDIUM: Final = 3
PRIORITY_HIGH: Final = 5

PRIORITY_MAP: Final = {
    0: "none",
    1: "low",
    3: "medium",
    5: "high",
}

# Configuration Keys
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_DUE_SOON_MINUTES: Final = "due_soon_minutes"
CONF_INCLUDE_COMPLETED: Final = "include_completed"

# Event Types
EVENT_TASK_CREATED: Final = "ticktick_task_created"
EVENT_TASK_COMPLETED: Final = "ticktick_task_completed"
EVENT_TASK_DUE_SOON: Final = "ticktick_task_due_soon"

# Platforms
PLATFORMS: Final = ["sensor", "calendar"]
