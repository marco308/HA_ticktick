"""The TickTick integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TickTickApi
from .const import DOMAIN, PLATFORMS
from .coordinator import TickTickDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

type TickTickConfigEntry = ConfigEntry[TickTickDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: TickTickConfigEntry) -> bool:
    """Set up TickTick from a config entry."""
    # Get the access token from the OAuth2 token data
    token_data = entry.data.get(CONF_TOKEN, {})
    access_token = token_data.get(CONF_ACCESS_TOKEN)

    if not access_token:
        _LOGGER.error("No access token found in config entry")
        return False

    # Create API client
    session = async_get_clientsession(hass)
    api = TickTickApi(session, access_token)

    # Create the coordinator
    coordinator = TickTickDataUpdateCoordinator(hass, api, entry)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator
    entry.runtime_data = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await async_setup_services(hass)

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: TickTickConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_update_options(hass: HomeAssistant, entry: TickTickConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up TickTick services."""
    # Services will be registered in services.py
    from .services import async_setup_services as setup_services

    await setup_services(hass)
