from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DogfyDietApi
from .const import CONF_REFRESH_TOKEN, DOMAIN
from .coordinator import DogfyDietCoordinator

PLATFORMS = [Platform.SENSOR]

type DogfyDietConfigEntry = ConfigEntry[DogfyDietCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: DogfyDietConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    api = DogfyDietApi(session, entry.data[CONF_REFRESH_TOKEN])

    coordinator = DogfyDietCoordinator(hass, api, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: DogfyDietConfigEntry
) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
