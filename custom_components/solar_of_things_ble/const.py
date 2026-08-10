"""Constants for Solar of Things BLE."""

DOMAIN = "solar_of_things_ble"
CONF_ADDRESS = "address"
CONF_AES_KEY = "aes_key"

DEFAULT_POLL_INTERVAL = 10

SERVICE_UUID = "0000fee7-0000-1000-8000-00805f9b34fb"
WRITE_UUID = "0000fed5-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fed6-0000-1000-8000-00805f9b34fb"

# Read-only request captured from the user's RWB1 while Solar of Things 3.1.11
# was performing local/proximal monitoring. Keeping the already-encrypted
# payload lets the integration verify real application-level communication with
# that logger even before the AES credential is recovered. It cannot be used
# to decode responses or change inverter settings.
CAPTURED_READ_PROBE_B64 = (
    "ix0+sJUFTmKKXhdFi2gMNhGMqzLyF0IufvVctPlNIuVi1aNAv9FZVxexwY87IPMnmK0seSQ3"
    "Fi8d6ppJOp853QO5DRG3sPyAobyKDbqdWSPSxYYfg528dMbzqgb/2yCBx0lwgPq1f0+7wL6V"
    "58QqkOFufg3TBn+DbpgtfWcLvunBP7RAUpbss5TWHcEdQ7shh1oYRuCMAinQ208pv3zbkA=="
)

# Protocol 44 command numbers captured from Solar of Things 3.1.11.
# They are metadata used by the RWB1 BLE bridge around the inverter's serial
# commands. All commands below are read-only.
READ_COMMANDS: tuple[tuple[str, str], ...] = (
    ("HSTS", "eo8w"),
    ("HGRID", "WdRR"),
    ("HOP", "2l0E"),
    ("HBAT", "2ONL"),
    ("HPV", "Mpod"),
    ("HTEMP", "V4W3"),
    ("HGEN", "COST"),
)
