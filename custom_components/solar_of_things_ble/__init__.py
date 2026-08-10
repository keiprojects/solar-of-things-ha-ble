"""Solar of Things BLE integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .ble import SolarOfThingsBLEClient
from .const import CONF_ADDRESS, CONF_AES_KEY, DOMAIN
from .coordinator import SolarOfThingsBLECoordinator
from .protocol import normalise_key

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one Solar of Things BLE data logger."""
    hass.data.setdefault(DOMAIN, {})
    client = SolarOfThingsBLEClient(
        hass,
        entry.data[CONF_ADDRESS],
        normalise_key(entry.data[CONF_AES_KEY]),
    )
    coordinator = SolarOfThingsBLECoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload and release the BLE connection."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if data:
            await data["client"].async_disconnect()
    return unload_ok
