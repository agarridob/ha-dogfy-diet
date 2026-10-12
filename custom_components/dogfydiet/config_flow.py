from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DogfyDietApi, DogfyDietAuthError
from .const import CONF_REFRESH_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)


def _login_schema(email: str | None = None) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_EMAIL, default=email or vol.UNDEFINED): str,
            vol.Required(CONF_PASSWORD): str,
        }
    )


class DogfyDietConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _async_login(
        self, user_input: dict[str, Any], errors: dict[str, str]
    ) -> dict[str, Any] | None:
        session = async_get_clientsession(self.hass)
        try:
            return await DogfyDietApi.login(
                session,
                user_input[CONF_EMAIL].strip().lower(),
                user_input[CONF_PASSWORD],
            )
        except DogfyDietAuthError:
            errors["base"] = "invalid_auth"
        except (aiohttp.ClientError, TimeoutError):
            errors["base"] = "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected error during login")
            errors["base"] = "unknown"
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            auth_data = await self._async_login(user_input, errors)
            if auth_data is not None:
                user_id = (
                    auth_data.get("userId")
                    or auth_data.get("user", {}).get("id")
                    or "default"
                )
                await self.async_set_unique_id(f"dogfydiet_{user_id}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Dogfy Diet",
                    data={
                        CONF_EMAIL: user_input[CONF_EMAIL].strip().lower(),
                        CONF_REFRESH_TOKEN: auth_data["refreshToken"],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_login_schema(),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()

        if user_input is not None:
            auth_data = await self._async_login(user_input, errors)
            if auth_data is not None:
                return self.async_update_reload_and_abort(
                    entry,
                    data={
                        **entry.data,
                        CONF_EMAIL: user_input[CONF_EMAIL].strip().lower(),
                        CONF_REFRESH_TOKEN: auth_data["refreshToken"],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=_login_schema(entry.data.get(CONF_EMAIL)),
            errors=errors,
        )
