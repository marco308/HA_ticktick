"""Config flow for TickTick integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TickTickApi, TickTickApiError, TickTickAuthError
from .const import (
    CLIENT_ID,
    CLIENT_SECRET,
    CONF_DUE_SOON_MINUTES,
    CONF_INCLUDE_COMPLETED,
    CONF_SCAN_INTERVAL,
    DEFAULT_DUE_SOON_MINUTES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)

_LOGGER = logging.getLogger(__name__)


class TickTickOAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler,
    domain=DOMAIN,
):
    """Handle TickTick OAuth2 config flow."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data that needs to be appended to the authorize url."""
        return {
            "scope": "tasks:read tasks:write",
        }

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create an entry for the flow."""
        # Validate the token works
        session = async_get_clientsession(self.hass)
        token = data.get(CONF_TOKEN, {})
        access_token = token.get(CONF_ACCESS_TOKEN)

        if not access_token:
            return self.async_abort(reason="invalid_auth")

        try:
            api = TickTickApi(session, access_token)
            await api.get_user_info()  # Validate token works
        except TickTickAuthError:
            return self.async_abort(reason="invalid_auth")
        except TickTickApiError as err:
            _LOGGER.error("Error connecting to TickTick: %s", err)
            return self.async_abort(reason="cannot_connect")

        # Use a unique ID based on the OAuth flow
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="TickTick",
            data=data,
        )


class TickTickConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TickTick."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> TickTickOptionsFlow:
        """Get the options flow for this handler."""
        return TickTickOptionsFlow(config_entry)

    async def async_step_user(
        self, _user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        # Check if already configured
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        return await self.async_step_pick_implementation()

    async def async_step_pick_implementation(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle picking OAuth implementation."""
        implementations = await config_entry_oauth2_flow.async_get_implementations(
            self.hass, DOMAIN
        )

        if not implementations:
            # Register the built-in OAuth2 implementation
            config_entry_oauth2_flow.async_register_implementation(
                self.hass,
                DOMAIN,
                config_entry_oauth2_flow.LocalOAuth2Implementation(
                    self.hass,
                    DOMAIN,
                    CLIENT_ID,
                    CLIENT_SECRET,
                    OAUTH2_AUTHORIZE,
                    OAUTH2_TOKEN,
                ),
            )

        return await TickTickOAuth2FlowHandler.async_step_pick_implementation(
            self, user_input
        )


class TickTickOptionsFlow(OptionsFlow):
    """Handle TickTick options."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                    vol.Optional(
                        CONF_DUE_SOON_MINUTES,
                        default=self.config_entry.options.get(
                            CONF_DUE_SOON_MINUTES, DEFAULT_DUE_SOON_MINUTES
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=120)),
                    vol.Optional(
                        CONF_INCLUDE_COMPLETED,
                        default=self.config_entry.options.get(
                            CONF_INCLUDE_COMPLETED, False
                        ),
                    ): bool,
                }
            ),
        )
