# Captured BLE protocol notes (secrets removed)

Observed on 2026-08-10 with Solar of Things 3.1.11 and an RWB1 logger.

- GATT service: `0000fee7-0000-1000-8000-00805f9b34fb`
- Command characteristic: `0000fed5-0000-1000-8000-00805f9b34fb`
- Response characteristic: `0000fed6-0000-1000-8000-00805f9b34fb`
- UART tunnel: 2400 baud, 8 data bits, no parity, 1 stop bit
- Request CID: 30024
- Response CID: 30025
- AES: 128-bit CBC
- IV: same 16 bytes as AES key
- Padding: zero bytes to a 16-byte boundary
- Encoding after encryption: Base64 ASCII
- Fragment header: byte 0 = 1-based index, byte 1 = total fragments, byte 2 = payload length
- Observed app payload chunk: 18 bytes before MTU negotiation; 192 bytes after negotiation
- Negotiated ATT MTU in the Android capture: 247

Read command metadata observed for gather protocol version code 44:

- HSTS -> eo8w
- HGRID -> WdRR
- HOP -> 2l0E
- HBAT -> 2ONL
- HPV -> Mpod
- HTEMP -> V4W3
- HGEN -> COST

No device/account token, DTU secret, station ID, or BLE AES key is stored in this package.
