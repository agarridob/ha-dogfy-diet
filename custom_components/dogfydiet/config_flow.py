from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DogfyDietApi, DogfyDietAuthError
from .const import CONF_REFRESH_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_REFRESH_TOKEN): str,
    }
)


class DogfyDietConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            refresh_token = user_input[CONF_REFRESH_TOKEN]
            session = async_get_clientsession(self.hass)

            try:
                auth_data = await DogfyDietApi.validate_refresh_token(
                    session, refresh_token
                )
            except DogfyDietAuthError:
                errors["base"] = "invalid_auth"
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"
            else:
                user_id = (
                    auth_data.get("userId")
                    or auth_data.get("user", {}).get("id")
                    or "default"
                )
                await self.async_set_unique_id(f"dogfydiet_{user_id}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Dogfy Diet",
                    data={CONF_REFRESH_TOKEN: refresh_token},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
