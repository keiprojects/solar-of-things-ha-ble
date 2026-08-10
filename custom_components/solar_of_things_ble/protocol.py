"""Solar of Things RWB1 BLE envelope and H-protocol decoder.

The BLE envelope was reconstructed from an Android Bluetooth HCI snoop capture.
The inverter field layout follows the documented H-family protocol used by the
POW-HVM6.2KP / HPVINV02 family.
"""
from __future__ import annotations

import base64
import json
from typing import Any

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

_AES_BLOCK_SIZE = 16

_UART = {
    "BaudRate": 2400,
    "DataBit": 8,
    "ParityBit": "NONE",
    "StopBit": 1,
}


def normalise_key(value: str) -> str:
    """Return a validated 128-bit AES key represented as 32 hex characters."""
    key = value.strip().replace(" ", "").replace(":", "").upper()
    if len(key) != 32:
        raise ValueError("BLE AES key must contain exactly 32 hexadecimal characters")
    try:
        bytes.fromhex(key)
    except ValueError as err:
        raise ValueError("BLE AES key contains non-hexadecimal characters") from err
    return key


def encrypt_envelope(payload: dict[str, Any], aes_key: str) -> bytes:
    """Encode one BLE JSON envelope exactly as the Solar of Things app does."""
    key = bytes.fromhex(normalise_key(aes_key))
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    raw += b"\x00" * ((-len(raw)) % _AES_BLOCK_SIZE)
    encryptor = Cipher(algorithms.AES(key), modes.CBC(key)).encryptor()
    encrypted = encryptor.update(raw) + encryptor.finalize()
    return base64.b64encode(encrypted)


def decrypt_envelope(payload: bytes, aes_key: str) -> dict[str, Any]:
    """Decode one reassembled BLE response envelope."""
    key = bytes.fromhex(normalise_key(aes_key))
    encrypted = base64.b64decode(payload, validate=True)
    if not encrypted or len(encrypted) % _AES_BLOCK_SIZE:
        raise ValueError("Invalid encrypted BLE payload length")
    decryptor = Cipher(algorithms.AES(key), modes.CBC(key)).decryptor()
    raw = (decryptor.update(encrypted) + decryptor.finalize()).rstrip(b"\x00")
    decoded = json.loads(raw.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("Unexpected BLE response type")
    return decoded


def fragment_payload(payload: bytes, chunk_size: int) -> list[bytes]:
    """Apply the RWB1 [index,total,length] fragmentation header."""
    if not 1 <= chunk_size <= 255:
        raise ValueError("chunk_size must be between 1 and 255")
    chunks = [payload[i : i + chunk_size] for i in range(0, len(payload), chunk_size)]
    if not chunks:
        chunks = [b""]
    if len(chunks) > 255:
        raise ValueError("BLE envelope requires too many fragments")
    total = len(chunks)
    return [
        bytes((index, total, len(chunk))) + chunk
        for index, chunk in enumerate(chunks, 1)
    ]


def build_read_request(command: str, cmd_no: str) -> dict[str, Any]:
    """Build the serial-tunnel request used by protocol version 44."""
    req = (command + "\r").encode("ascii").hex().upper()
    return {
        "CID": 30024,
        "PL": {
            "Req": req,
            "Uart": dict(_UART),
            "CmdType": "gatherSingleDevProps",
            "CmdNo": cmd_no,
        },
    }


def extract_serial_response(envelope: dict[str, Any]) -> str:
    """Extract and decode PL.Rsp from a CID 30025 response."""
    if envelope.get("CID") != 30025:
        raise ValueError(f"Unexpected response CID: {envelope.get('CID')!r}")
    if envelope.get("RC") not in (0, "0", None):
        raise ValueError(f"BLE bridge returned RC={envelope.get('RC')!r}")
    pl = envelope.get("PL")
    if not isinstance(pl, dict) or not isinstance(pl.get("Rsp"), str):
        raise ValueError("BLE response does not contain PL.Rsp")
    try:
        raw = bytes.fromhex(pl["Rsp"])
    except ValueError as err:
        raise ValueError("PL.Rsp is not valid hexadecimal data") from err
    text = raw.decode("ascii", errors="replace").rstrip("\r\n\x00")
    if text.startswith("("):
        text = text[1:]
    return text


def _float(parts: list[str], index: int) -> float | None:
    if index >= len(parts):
        return None
    try:
        return float(parts[index])
    except (TypeError, ValueError):
        return None


def _set(out: dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        out[key] = value


def parse_h_response(command: str, response: str) -> dict[str, Any]:
    """Decode useful fields from one H-family response."""
    parts = response.strip().split()
    out: dict[str, Any] = {}

    if command == "HGRID":
        _set(out, "grid_voltage_v", _float(parts, 0))
        _set(out, "grid_frequency_hz", _float(parts, 1))
        mains_power = _float(parts, 6)
        _set(out, "grid_power_w", mains_power)
        if mains_power is not None:
            out["grid_import_power_w"] = max(mains_power, 0.0)
            out["grid_export_power_w"] = max(-mains_power, 0.0)
        if len(parts) > 7:
            out["grid_flow_direction_code"] = parts[7]

    elif command == "HOP":
        _set(out, "output_voltage_v", _float(parts, 0))
        _set(out, "output_frequency_hz", _float(parts, 1))
        _set(out, "output_apparent_power_va", _float(parts, 2))
        active_power = _float(parts, 3)
        _set(out, "output_active_power_w", active_power)
        _set(out, "load_power_w", active_power)
        _set(out, "output_load_percent", _float(parts, 4))

    elif command == "HBAT":
        if parts:
            out["battery_type_code"] = parts[0]
        _set(out, "battery_voltage_v", _float(parts, 1))
        _set(out, "battery_soc_percent", _float(parts, 2))
        _set(out, "battery_charging_current_a", _float(parts, 3))
        _set(out, "battery_discharge_current_a", _float(parts, 4))
        _set(out, "bus_voltage_v", _float(parts, 5))

    elif command == "HPV":
        _set(out, "pv_voltage_v", _float(parts, 0))
        _set(out, "pv_current_a", _float(parts, 1))
        _set(out, "pv_power_w", _float(parts, 2))

    elif command == "HTEMP":
        _set(out, "inverter_temperature_c", _float(parts, 0))
        _set(out, "boost_temperature_c", _float(parts, 1))
        _set(out, "transformer_temperature_c", _float(parts, 2))
        _set(out, "pv_temperature_c", _float(parts, 3))
        _set(out, "fan_1_speed_percent", _float(parts, 4))
        _set(out, "fan_2_speed_percent", _float(parts, 5))

    elif command == "HGEN":
        if len(parts) > 0:
            out["generation_date"] = parts[0]
        if len(parts) > 1:
            out["generation_time"] = parts[1]
        _set(out, "daily_generation_kwh", _float(parts, 2))
        _set(out, "monthly_generation_kwh", _float(parts, 3))
        _set(out, "yearly_generation_kwh", _float(parts, 4))
        _set(out, "total_generation_kwh", _float(parts, 5))

    elif command == "HSTS":
        if parts:
            out["status_code"] = parts[0]
        if len(parts) > 1:
            packed = parts[1]
            mode_code = packed[0] if packed else ""
            out["mode_code"] = mode_code
            out["inverter_mode"] = {
                "B": "Battery Mode",
                "L": "Mains Mode",
            }.get(mode_code, mode_code or "Unknown")
            out["status_bits"] = packed[1:] if len(packed) > 1 else ""
        if len(parts) > 2:
            out["fault_bits"] = parts[2]

    return out


def finalise_telemetry(values: dict[str, Any]) -> dict[str, Any]:
    """Add stable calculated values after all command responses are merged."""
    result = dict(values)
    voltage = result.get("battery_voltage_v")
    charging = result.get("battery_charging_current_a")
    discharging = result.get("battery_discharge_current_a")
    if isinstance(voltage, (int, float)) and (
        isinstance(charging, (int, float)) or isinstance(discharging, (int, float))
    ):
        # Positive = charging into the battery; negative = discharge to the load.
        result["battery_power_w"] = voltage * ((charging or 0.0) - (discharging or 0.0))
    return result
