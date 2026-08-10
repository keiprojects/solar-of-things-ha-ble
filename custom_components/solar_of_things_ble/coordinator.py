"""Update coordinator for Solar of Things BLE."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .ble import SolarOfThingsBLEClient
from .const import DEFAULT_POLL_INTERVAL, DOMAIN


class SolarOfThingsBLECoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll live inverter telemetry over the local BLE tunnel."""

    def __init__(self, hass: HomeAssistant, client: SolarOfThingsBLEClient) -> None:
        self.client = client
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=f"{DOMAIN}_{client.address}",
            update_interval=timedelta(seconds=DEFAULT_POLL_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            values = await self.client.async_poll()
        except Exception as err:
            raise UpdateFailed(f"Local BLE poll failed: {err}") from err
        values["updated_at"] = datetime.now(timezone.utc).isoformat()
        values["telemetry_source"] = "local_ble"
        return values
