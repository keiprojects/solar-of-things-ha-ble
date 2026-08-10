"""Small protocol regression tests that do not require Home Assistant."""
from __future__ import annotations

import importlib.util
from pathlib import Path

PROTOCOL_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "solar_of_things_ble"
    / "protocol.py"
)
SPEC = importlib.util.spec_from_file_location("solar_of_things_ble_protocol", PROTOCOL_PATH)
assert SPEC is not None and SPEC.loader is not None
protocol = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(protocol)

KEY = "00112233445566778899AABBCCDDEEFF"


def test_envelope_round_trip():
    payload = protocol.build_read_request("HSTS", "eo8w")
    assert protocol.decrypt_envelope(protocol.encrypt_envelope(payload, KEY), KEY) == payload


def test_fragmentation_round_trip():
    payload = b"abcdefghijklmnopqrstuvwxyz"
    frames = protocol.fragment_payload(payload, 10)
    assert b"".join(frame[3:] for frame in frames) == payload
    assert [frame[:3] for frame in frames] == [
        bytes((1, 3, 10)),
        bytes((2, 3, 10)),
        bytes((3, 3, 6)),
    ]


def test_core_h_fields():
    grid = protocol.parse_h_response(
        "HGRID", "240.2 49.9 280 090 70 40 +00291 0 06500 11+00000"
    )
    assert grid["grid_voltage_v"] == 240.2
    assert grid["grid_import_power_w"] == 291.0
    assert grid["grid_export_power_w"] == 0.0

    output = protocol.parse_h_response("HOP", "240.2 49.9 00216 00177 003")
    assert output["load_power_w"] == 177.0

    status = protocol.parse_h_response(
        "HSTS", "00 B010000000000 10211002100B127000000"
    )
    assert status["inverter_mode"] == "Battery Mode"
    assert status["status_code"] == "00"


def test_battery_power_sign():
    charging = protocol.finalise_telemetry(
        {
            "battery_voltage_v": 50.0,
            "battery_charging_current_a": 10.0,
            "battery_discharge_current_a": 0.0,
        }
    )
    discharging = protocol.finalise_telemetry(
        {
            "battery_voltage_v": 50.0,
            "battery_charging_current_a": 0.0,
            "battery_discharge_current_a": 10.0,
        }
    )
    assert charging["battery_power_w"] == 500.0
    assert discharging["battery_power_w"] == -500.0
