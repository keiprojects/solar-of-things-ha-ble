"""BLE transport for the Solar of Things RWB1 data logger."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from bleak import BleakClient
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant

from .const import NOTIFY_UUID, READ_COMMANDS, SERVICE_UUID, WRITE_UUID
from .protocol import (
    build_read_request,
    decrypt_envelope,
    encrypt_envelope,
    extract_serial_response,
    finalise_telemetry,
    fragment_payload,
    parse_h_response,
)

_LOGGER = logging.getLogger(__name__)


class SolarOfThingsBLEError(RuntimeError):
    """Base BLE transport error."""


class SolarOfThingsBLEClient:
    """Maintain one local BLE connection and issue sequential read commands."""

    def __init__(self, hass: HomeAssistant, address: str, aes_key: str) -> None:
        self.hass = hass
        self.address = address.upper()
        self.aes_key = aes_key
        self._client: BleakClient | None = None
        self._command_lock = asyncio.Lock()
        self._response_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._rx_parts: dict[int, bytes] = {}
        self._rx_total: int | None = None

    def _disconnected(self, _client: BleakClient) -> None:
        self._client = None
        self._rx_parts.clear()
        self._rx_total = None

    async def _ensure_connected(self) -> BleakClient:
        if self._client is not None and self._client.is_connected:
            return self._client

        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if ble_device is None:
            raise SolarOfThingsBLEError(
                f"Bluetooth device {self.address} is not currently reachable "
                "by a connectable Home Assistant Bluetooth adapter"
            )

        client = BleakClient(
            ble_device,
            disconnected_callback=self._disconnected,
            timeout=20.0,
        )
        try:
            await client.connect()
            if client.services.get_service(SERVICE_UUID) is None:
                raise SolarOfThingsBLEError(
                    f"Device {self.address} does not expose Solar of Things service FEE7"
                )
            if client.services.get_characteristic(WRITE_UUID) is None:
                raise SolarOfThingsBLEError("Solar of Things write characteristic FED5 not found")
            if client.services.get_characteristic(NOTIFY_UUID) is None:
                raise SolarOfThingsBLEError("Solar of Things response characteristic FED6 not found")
            await client.start_notify(NOTIFY_UUID, self._notification)
        except Exception:
            try:
                await client.disconnect()
            except Exception:  # pragma: no cover - best effort cleanup
                pass
            raise

        self._client = client
        _LOGGER.debug(
            "Connected to Solar of Things BLE device %s (MTU %s)",
            self.address,
            client.mtu_size,
        )
        return client

    def _notification(self, _sender: Any, data: bytearray) -> None:
        raw = bytes(data)
        if len(raw) < 3:
            _LOGGER.debug("Ignoring short Solar of Things BLE fragment")
            return

        index, total, length = raw[0], raw[1], raw[2]
        fragment = raw[3 : 3 + length]
        if index < 1 or total < 1 or index > total or len(fragment) != length:
            _LOGGER.debug("Ignoring malformed Solar of Things BLE fragment")
            return

        if index == 1:
            self._rx_parts = {}
            self._rx_total = total
        if self._rx_total != total:
            self._rx_parts = {}
            self._rx_total = total

        self._rx_parts[index] = fragment
        if all(part in self._rx_parts for part in range(1, total + 1)):
            payload = b"".join(self._rx_parts[part] for part in range(1, total + 1))
            self._rx_parts = {}
            self._rx_total = None
            try:
                decoded = decrypt_envelope(payload, self.aes_key)
            except Exception as err:
                _LOGGER.debug("Could not decrypt Solar of Things BLE response: %s", err)
                return
            self._response_queue.put_nowait(decoded)

    async def _send_read(self, command: str, cmd_no: str) -> str:
        async with self._command_lock:
            client = await self._ensure_connected()

            while not self._response_queue.empty():
                try:
                    self._response_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

            envelope = build_read_request(command, cmd_no)
            encrypted = encrypt_envelope(envelope, self.aes_key)

            # ATT write payload is MTU-3. Reserve another 3 bytes for the RWB1
            # fragment header. The Android app used 18-byte fragments before
            # MTU negotiation and capped its larger fragments at 192 bytes.
            mtu = getattr(client, "mtu_size", 23) or 23
            chunk_size = max(18, min(192, int(mtu) - 6))
            for fragment in fragment_payload(encrypted, chunk_size):
                await client.write_gatt_char(WRITE_UUID, fragment, response=True)

            try:
                async with asyncio.timeout(4.0):
                    response = await self._response_queue.get()
            except TimeoutError as err:
                raise SolarOfThingsBLEError(
                    f"Timed out waiting for {command} response"
                ) from err

            return extract_serial_response(response)

    async def async_poll(self) -> dict[str, Any]:
        """Poll the read-only live command set and return merged telemetry."""
        values: dict[str, Any] = {}
        try:
            for command, cmd_no in READ_COMMANDS:
                raw = await self._send_read(command, cmd_no)
                _LOGGER.debug("%s -> %s", command, raw)
                values.update(parse_h_response(command, raw))
        except Exception:
            await self.async_disconnect()
            raise
        return finalise_telemetry(values)

    async def async_disconnect(self) -> None:
        """Stop notifications and close the active GATT connection."""
        client = self._client
        self._client = None
        self._rx_parts.clear()
        self._rx_total = None
        if client is not None and client.is_connected:
            try:
                await client.stop_notify(NOTIFY_UUID)
            except Exception:
                pass
            try:
                await client.disconnect()
            except Exception:
                pass
