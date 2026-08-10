"""Sensors for Solar of Things BLE."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ADDRESS, DOMAIN


@dataclass(frozen=True, kw_only=True)
class SolarBLESensorDescription(SensorEntityDescription):
    """Describe a BLE telemetry sensor."""


SENSORS: tuple[SolarBLESensorDescription, ...] = (
    SolarBLESensorDescription(
        key="probe_status",
        name="BLE Probe Status",
        icon="mdi:bluetooth-connect",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SolarBLESensorDescription(
        key="probe_response_bytes",
        name="BLE Probe Response Bytes",
        icon="mdi:message-reply-text-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SolarBLESensorDescription(
        key="pv_power_w", name="PV Input Power", device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT, state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
    ),
    SolarBLESensorDescription(
        key="pv_voltage_v", name="PV Voltage", device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT, state_class=SensorStateClass.MEASUREMENT,
    ),
    SolarBLESensorDescription(
        key="pv_current_a", name="PV Current", device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, state_class=SensorStateClass.MEASUREMENT,
    ),
    SolarBLESensorDescription(
        key="load_power_w", name="Load Power", device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT, state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:home-lightning-bolt",
    ),
    SolarBLESensorDescription(
        key="output_active_power_w", name="AC Output Power", device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT, state_class=SensorStateClass.MEASUREMENT,
    ),
    SolarBLESensorDescription(
        key="output_apparent_power_va", name="AC Output Apparent Power",
        device_class=SensorDeviceClass.APPARENT_POWER, native_unit_of_measurement="VA",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SolarBLESensorDescription(
        key="output_voltage_v", name="Output Voltage", device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT, state_class=SensorStateClass.MEASUREMENT,
    ),
    SolarBLESensorDescription(
        key="output_frequency_hz", name="Output Frequency", device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ, state_class=SensorStateClass.MEASUREMENT,
    ),
    SolarBLESensorDescription(
        key="output_load_percent", name="Output Load Percent", native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT, icon="mdi:gauge",
    ),
    SolarBLESensorDescription(
        key="grid_import_power_w", name="Grid Import Power", device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT, state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower-import",
    ),
    SolarBLESensorDescription(
        key="grid_export_power_w", name="Grid Export Power", device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT, state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower-export",
    ),
    SolarBLESensorDescription(
        key="grid_voltage_v", name="AC Input Voltage", device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT, state_class=SensorStateClass.MEASUREMENT,
    ),
    SolarBLESensorDescription(
        key="grid_frequency_hz", name="AC Input Frequency", device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ, state_class=SensorStateClass.MEASUREMENT,
    ),
    SolarBLESensorDescription(
        key="battery_power_w", name="Battery Power", device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT, state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging",
    ),
    SolarBLESensorDescription(
        key="battery_voltage_v", name="Battery Voltage", device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT, state_class=SensorStateClass.MEASUREMENT,
    ),
    SolarBLESensorDescription(
        key="battery_soc_percent", name="Battery State of Charge", device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT,
    ),
    SolarBLESensorDescription(
        key="battery_charging_current_a", name="Battery Charging Current", device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-arrow-up",
    ),
    SolarBLESensorDescription(
        key="battery_discharge_current_a", name="Battery Discharge Current", device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-arrow-down",
    ),
    SolarBLESensorDescription(key="inverter_mode", name="Operating Mode", icon="mdi:state-machine"),
    SolarBLESensorDescription(
        key="inverter_temperature_c", name="Inverter Temperature", device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT,
    ),
    SolarBLESensorDescription(
        key="daily_generation_kwh", name="Daily PV Generation", device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:solar-power",
    ),
    SolarBLESensorDescription(
        key="monthly_generation_kwh", name="Monthly PV Generation", device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:solar-power",
    ),
    SolarBLESensorDescription(
        key="yearly_generation_kwh", name="Yearly PV Generation", device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:solar-power",
    ),
    SolarBLESensorDescription(
        key="total_generation_kwh", name="Total PV Generation", device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:solar-power",
    ),
    SolarBLESensorDescription(key="status_code", name="Status Code", icon="mdi:list-status"),
    SolarBLESensorDescription(key="fault_bits", name="Fault Code", icon="mdi:alert-circle-outline"),
    SolarBLESensorDescription(
        key="boost_temperature_c", name="Boost Temperature", device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT,
    ),
    SolarBLESensorDescription(
        key="transformer_temperature_c", name="Transformer Temperature", device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT,
    ),
    SolarBLESensorDescription(
        key="pv_temperature_c", name="PV Temperature", device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT,
    ),
    SolarBLESensorDescription(
        key="fan_1_speed_percent", name="Fan 1 Speed", native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT, icon="mdi:fan",
    ),
    SolarBLESensorDescription(
        key="fan_2_speed_percent", name="Fan 2 Speed", native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT, icon="mdi:fan",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create all local BLE telemetry sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    address = entry.data[CONF_ADDRESS]
    async_add_entities(
        SolarOfThingsBLESensor(coordinator, address, description)
        for description in SENSORS
    )


class SolarOfThingsBLESensor(CoordinatorEntity, SensorEntity):
    """One value from the merged BLE snapshot."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, address: str, description: SolarBLESensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._address = address
        self._attr_unique_id = (
            f"{DOMAIN}_{address.replace(':', '').lower()}_{description.key}"
        )

    @property
    def native_value(self) -> Any:
        return (self.coordinator.data or {}).get(self.entity_description.key)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._address)},
            "connections": {("bluetooth", self._address)},
            "name": f"Solar of Things BLE {self._address[-5:]}",
            "manufacturer": "Siseli / WiFi Relabs",
            "model": "RWB1 BLE data logger",
        }

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        return {
            "telemetry_source": data.get("telemetry_source"),
            "updated_at": data.get("updated_at"),
        }
