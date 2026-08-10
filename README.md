# Solar of Things BLE for Home Assistant

Local Bluetooth integration for the Siseli / WiFi Relabs **RWB1** data logger used by Solar of Things with the **POW-HVM6.2KP / HPVINV02** H-family inverter protocol.

## Current status

**v0.1.2 — hardware-specific read-only beta**

Two modes are available:

- **Keyless diagnostic mode:** only the BLE address is required. Setup validates the real RWB1 GATT service (`FEE7`, `FED5`, `FED6`) and adds the device even if the encrypted application probe does not answer.
- **Decoded telemetry mode:** when the Solar of Things application AES key is available, requests and responses are encrypted/decrypted and inverter telemetry is exposed.

No inverter setting writes are enabled.

## What the Android HCI capture proves

The official Solar of Things app uses:

- Service: `0000fee7-0000-1000-8000-00805f9b34fb`
- Write characteristic: `0000fed5-0000-1000-8000-00805f9b34fb`
- Indication characteristic: `0000fed6-0000-1000-8000-00805f9b34fb`
- UART tunnel: **2400 baud, 8-N-1**
- Request CID: `30024`
- Response CID: `30025`
- AES: **128-bit CBC**
- Encoding: Base64
- RWB1 fragment header: `[index, total, payload length]`

The capture also shows the same 216-byte application request being sent as many small fragments at a small ATT MTU and as **one 216-byte fragment** once a larger MTU is available. v0.1.2 now uses the negotiated MTU instead of artificially capping request fragments at 192 bytes.

## Install / update through HACS

1. Open **HACS → Integrations**.
2. Open **Solar of Things BLE**.
3. Update/redownload to **v0.1.2**.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services**.
6. Use the automatically discovered **Solar of Things BLE** device, or add the integration manually.

## Test without an AES key

1. Completely close **Solar of Things Proximal Monitoring** on the phone.
2. Add the discovered RWB1.
3. Leave **BLE AES key** blank.
4. Submit.

If Home Assistant can connect to the expected `FEE7/FED5/FED6` GATT service, setup now succeeds even if the encrypted replay receives no reply.

After setup, inspect:

- **BLE Probe Status**
  - `responding` = an encrypted `FED6` application response was received
  - `no_response` = GATT is connected but the replay did not receive an application response
- **BLE Probe Response Bytes**
  - greater than `0` when a complete encrypted application response was received

This distinction lets us debug the real logger without Home Assistant rejecting the integration during setup.

## Debug logging

```yaml
logger:
  default: info
  logs:
    custom_components.solar_of_things_ble: debug
```

v0.1.2 debug output includes:

- successful GATT connection
- `FED5` write size, negotiated MTU, chunk size and fragment count
- every `FED6` fragment index/total/length
- completed encrypted response size

The AES key is never logged.

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

When decoded mode is available, the integration exposes PV, load, grid, battery, operating mode, temperatures, energy generation and status/fault data.

Battery power uses:

```text
battery_voltage × (charging_current - discharge_current)
```

So **charging is positive** and **discharging is negative**.

## Next target

Automatically obtain the BLE application credential from the authenticated Solar of Things account/device so the AES key does not need to be entered manually.

## License

MIT
