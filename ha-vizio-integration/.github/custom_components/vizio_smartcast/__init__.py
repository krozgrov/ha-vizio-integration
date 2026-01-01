"""The vizio component."""

from __future__ import annotations

from typing import Any

from homeassistant.components.media_player import MediaPlayerDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_CLASS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import CONF_APPS, DOMAIN
from .coordinator import VizioAppsDataUpdateCoordinator

PLATFORMS = [Platform.MEDIA_PLAYER]


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old config entries to new format if needed."""
    if config_entry.version == 1:
        # Future migration logic can be added here
        # For now, just return True to indicate migration is complete
        return True
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Load the saved entities."""
    # Migrate config entry if needed
    await async_migrate_entry(hass, entry)

    hass.data.setdefault(DOMAIN, {})
    if (
        CONF_APPS not in hass.data[DOMAIN]
        and entry.data[CONF_DEVICE_CLASS] == MediaPlayerDeviceClass.TV
    ):
        store: Store[list[dict[str, Any]]] = Store(hass, 1, DOMAIN)
        coordinator = VizioAppsDataUpdateCoordinator(hass, entry, store)
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN][CONF_APPS] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if not any(
        entry.data[CONF_DEVICE_CLASS] == MediaPlayerDeviceClass.TV
        for entry in hass.config_entries.async_loaded_entries(DOMAIN)
    ):
        hass.data[DOMAIN].pop(CONF_APPS, None)

    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)

    return unload_ok