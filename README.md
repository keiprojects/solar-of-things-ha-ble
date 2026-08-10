# Solar of Things BLE for Home Assistant

Local Bluetooth integration for the Siseli / WiFi Relabs **RWB1** data logger used by Solar of Things with the **POW-HVM6.2KP / HPVINV02** H-family inverter protocol.

This project reads the inverter directly over Bluetooth. It does **not** require the Siseli cloud for telemetry.

## Current status

**v0.1.0 — hardware-specific read-only beta**

The BLE transport was reconstructed from an Android HCI capture of Solar of Things 3.1.11. The H-family field layout was cross-checked against the MIT-licensed `kOld/solarplug-esphome` protocol documentation for the same inverter family.

Remote setting writes are intentionally disabled until the read path is proven stable on hardware.

## BLE protocol

- Service: `0000fee7-0000-1000-8000-00805f9b34fb`
- Write characteristic: `0000fed5-0000-1000-8000-00805f9b34fb`
- Response characteristic: `0000fed6-0000-1000-8000-00805f9b34fb`
- UART tunnel: **2400 baud, 8 data bits, no parity, 1 stop bit**
- Request CID: `30024`
- Response CID: `30025`
- AES: **128-bit CBC**
- IV: same 16 bytes as the AES key
- Padding: zero bytes to a 16-byte boundary
- Encrypted payload encoding: Base64 ASCII
- Fragment header: `[1-based index, total fragments, payload length]`
- Poll interval: **10 seconds**

The integration uses Home Assistant's shared Bluetooth stack, so it can use a local HA Bluetooth adapter or a compatible connectable Bluetooth proxy.

## Read commands

| Command | Captured CmdNo |
|---|---|
| `HSTS` | `eo8w` |
| `HGRID` | `WdRR` |
| `HOP` | `2l0E` |
| `HBAT` | `2ONL` |
| `HPV` | `Mpod` |
| `HTEMP` | `V4W3` |
| `HGEN` | `COST` |

## Main sensors

The integration exposes the core review set plus additional diagnostics:

1. PV Input Power
2. PV Voltage
3. PV Current
4. Load Power
5. Output Voltage
6. Output Load Percent
7. Grid Import Power
8. AC Input Voltage
9. Battery Power
10. Battery Voltage
11. Battery State of Charge
12. Battery Charging Current
13. Battery Discharge Current
14. Operating Mode
15. Inverter Temperature
16. Daily PV Generation
17. Monthly PV Generation
18. Yearly PV Generation
19. Total PV Generation
20. Status Code / Fault Code

Additional entities include output apparent power/frequency, grid export/frequency, boost/transformer/PV temperatures, and fan speeds.

Battery power follows this sign convention:

```text
battery_voltage × (charging_current - discharge_current)
```

So **charging is positive** and **discharging is negative**.

## Installation

### HACS custom repository

1. In HACS, open **Integrations**.
2. Open **Custom repositories**.
3. Add this repository as category **Integration**.
4. Download **Solar of Things BLE**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration → Solar of Things BLE**.

### Manual

Copy:

```text
custom_components/solar_of_things_ble
```

to:

```text
/config/custom_components/solar_of_things_ble
```

Then restart Home Assistant.

## Configuration

You need:

- the BLE address of the RWB1 / WiFi Relabs logger
- its 128-bit BLE AES key as **32 hexadecimal characters**

For an Android bug report captured while Solar of Things is using Proximal Monitoring, the key can be located by searching the bug report text for:

```text
string aesKey:
```

Do **not** publish the bug report or AES key in a GitHub issue. Android bug reports can contain account/session and device secrets.

## Bluetooth discovery

Home Assistant will offer discovery when a connectable device advertising service `FEE7` is seen. You can also add the integration manually and enter the BLE address.

Close Solar of Things **Proximal Monitoring** while testing. The logger may only support one active BLE client at a time.

## Debug logging

```yaml
logger:
  default: info
  logs:
    custom_components.solar_of_things_ble: debug
```

The debug log shows the decrypted inverter H-command responses, but the integration never logs the configured AES key.

## Safety / scope

v0.1.0 is read-only. It does not send inverter configuration commands or change operating parameters.

## License

MIT
