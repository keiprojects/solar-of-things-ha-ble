"""Constants for Solar of Things BLE."""

DOMAIN = "solar_of_things_ble"
CONF_ADDRESS = "address"
CONF_AES_KEY = "aes_key"

DEFAULT_POLL_INTERVAL = 10

SERVICE_UUID = "0000fee7-0000-1000-8000-00805f9b34fb"
WRITE_UUID = "0000fed5-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fed6-0000-1000-8000-00805f9b34fb"

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
