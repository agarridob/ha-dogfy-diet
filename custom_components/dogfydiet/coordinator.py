from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DogfyDietApi, DogfyDietApiError, DogfyDietAuthError
from .const import CONF_REFRESH_TOKEN, DOMAIN, UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)


class DogfyDietCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self, hass: HomeAssistant, api: DogfyDietApi, entry: ConfigEntry
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )
        self.api = api
        self._entry = entry

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            profile = await self.api.get_self()
            orders_resp = await self.api.get_orders()
            orders = orders_resp.get("docs", [])

            if self.api.refresh_token != self._entry.data[CONF_REFRESH_TOKEN]:
                self.hass.config_entries.async_update_entry(
                    self._entry,
                    data={
                        **self._entry.data,
                        CONF_REFRESH_TOKEN: self.api.refresh_token,
                    },
                )

            return {
                "profile": profile,
                "dogs": profile.get("dogs", []),
                "subscription": profile.get("subscription", {}),
                "orders": orders,
            }
        except DogfyDietAuthError as err:
            raise ConfigEntryAuthFailed(
                "Refresh token expired — reauthentication required"
            ) from err
        except DogfyDietApiError as err:
            raise UpdateFailed(f"Error fetching Dogfy Diet data: {err}") from err
