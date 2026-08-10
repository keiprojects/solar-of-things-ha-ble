# Solar of Things BLE for Home Assistant

Local Bluetooth integration for the Siseli / WiFi Relabs **RWB1** data logger used by Solar of Things with the **POW-HVM6.2KP / HPVINV02** H-family inverter protocol.

## Current status

**v0.1.1 — hardware-specific read-only beta**

There are now two modes:

- **Keyless probe mode:** only the BLE address is required. Home Assistant connects to the RWB1, subscribes to `FED6`, replays a captured **read-only** Solar of Things request on `FED5`, and checks that the logger actually replies.
- **Decoded telemetry mode:** if the Solar of Things application AES key is available, the integration generates requests and decrypts responses to expose inverter telemetry.

The keyless probe does **not** change any inverter settings.

## What the Android capture proved

The official Solar of Things app did not perform a separate BLE authentication handshake after connection. In the captured session it connected, enabled indications, wrote an encrypted application packet to `FED5`, then received the encrypted reply on `FED6`.

So we can already test real application-level communication without knowing the AES key. The key is only still required to decode the reply into inverter values.

## BLE protocol

- Service: `0000fee7-0000-1000-8000-00805f9b34fb`
- Write: `0000fed5-0000-1000-8000-00805f9b34fb`
- Response: `0000fed6-0000-1000-8000-00805f9b34fb`
- UART tunnel: **2400 baud, 8-N-1**
- Request CID: `30024`
- Response CID: `30025`
- AES: **128-bit CBC**
- Encoding: Base64
- Fragment header: `[index, total, payload length]`
- Poll interval: **10 seconds**

## Install / update through HACS

1. Open **HACS → Integrations**.
2. If the repository is not already added, add this repository as a **Custom repository → Integration**.
3. Download/update **Solar of Things BLE** to **v0.1.1**.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration → Solar of Things BLE**.

## Test it without an AES key

1. Completely close **Solar of Things Proximal Monitoring** on the phone.
2. Add **Solar of Things BLE** in Home Assistant.
3. Choose or enter the RWB1 BLE address.
4. **Leave `BLE AES key` blank.**
5. Submit.

If the RWB1 accepts the captured read packet, setup succeeds and these diagnostic entities appear:

- **BLE Probe Status** → `responding`
- **BLE Probe Response Bytes** → size of the encrypted application reply

That confirms:

```text
Home Assistant → BLE → FED5 → RWB1 → inverter bridge → FED6 → Home Assistant
```

It does not yet decode the encrypted reply.

## Decoded read commands

| Command | Captured CmdNo |
|---|---|
| `HSTS` | `eo8w` |
| `HGRID` | `WdRR` |
| `HOP` | `2l0E` |
| `HBAT` | `2ONL` |
| `HPV` | `Mpod` |
| `HTEMP` | `V4W3` |
| `HGEN` | `COST` |

When the AES credential is available, the integration exposes PV power/voltage/current, load power, output voltage/load %, grid import/export, battery power/voltage/SOC/current, operating mode, temperatures, generation totals, status/fault information and other diagnostics.

Battery power uses:

```text
battery_voltage × (charging_current - discharge_current)
```

So **charging is positive** and **discharging is negative**.

## Debug logging

```yaml
logger:
  default: info
  logs:
    custom_components.solar_of_things_ble: debug
```

The keyless probe logs response size plus only a short encrypted prefix. A configured AES key is never logged.

## Next target

The next step is automatic retrieval of the application BLE credential from an authenticated Solar of Things account/device, so decoded mode will not require manually entering the AES key.

## License

MIT
