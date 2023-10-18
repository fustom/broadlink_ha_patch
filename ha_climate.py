"""Support for Broadlink climate devices."""
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
    ATTR_CURRENT_TEMPERATURE,
    ATTR_HVAC_ACTION,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_HALVES,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .entity import BroadlinkEntity
from .device import BroadlinkDevice


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Broadlink climate entities."""
    device = hass.data[DOMAIN].devices[config_entry.entry_id]

    if device.api.type in {"HYS"}:
        climate_entities = [BroadlinkThermostat(device)]
        async_add_entities(climate_entities)


class BroadlinkThermostat(BroadlinkEntity, ClimateEntity, RestoreEntity):
    """Representation of a Broadlink Hysen climate entity."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, device: BroadlinkDevice) -> None:
        """Initialize the climate entity."""
        super().__init__(device)
        self._attr_hvac_action = None
        self._attr_hvac_mode = None
        self._attr_current_temperature = None
        self._attr_target_temperature = None
        self._attr_unique_id = device.unique_id
        self.sensor = 0

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        return ClimateEntityFeature.TARGET_TEMPERATURE

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs[ATTR_TEMPERATURE]
        await self._device.async_request(self._device.api.set_temp, temperature)
        self._attr_target_temperature = temperature
        self.async_write_ha_state()

    @property
    def target_temperature_step(self) -> float:
        """Return the supported step of target temperature."""
        return PRECISION_HALVES

    @property
    def temperature_unit(self) -> UnitOfTemperature:
        """Return the unit of measurement that is used."""
        return UnitOfTemperature.CELSIUS

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available hvac operation modes.

        Need to be a subset of HVAC_MODES.
        """
        return [HVACMode.HEAT, HVACMode.COOL, HVACMode.OFF, HVACMode.AUTO]

    @callback
    def _update_state(self, data: Any):
        """Update data."""
        self.sensor = data["sensor"]
        if data["power"]:
            if data["auto_mode"]:
                self._attr_hvac_mode = HVACMode.AUTO
            else:
                if data["heating_cooling"]:
                    self._attr_hvac_mode = HVACMode.COOL
                else:
                    self._attr_hvac_mode = HVACMode.HEAT

            if data["active"]:
                if data["heating_cooling"]:
                    self._attr_hvac_action = HVACAction.COOLING
                else:
                    self._attr_hvac_action = HVACAction.HEATING
            else:
                self._attr_hvac_action = HVACAction.IDLE
        else:
            self._attr_hvac_mode = HVACMode.OFF
            self._attr_hvac_action = HVACAction.OFF
        if self.sensor:
            self._attr_current_temperature = data["external_temp"]
        else:
            self._attr_current_temperature = data["room_temp"]
        self._attr_target_temperature = data["thermostat_temp"]

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self._device.async_request(self._device.api.set_power, 0)

        elif hvac_mode == HVACMode.AUTO:
            await self._device.async_request(self._device.api.set_power, 1)
            await self._device.async_request(self._device.api.set_mode, 1, 0, self.sensor)

        elif hvac_mode == HVACMode.HEAT:
            await self._device.async_request(self._device.api.set_power, 1)
            await self._device.async_request(self._device.api.set_mode, 0, 0, self.sensor)

        elif hvac_mode == HVACMode.COOL:
            await self._device.async_request(self._device.api.set_power, 1, 0, 1)
            await self._device.async_request(self._device.api.set_mode, 0, 0, self.sensor)

        self._attr_hvac_mode = hvac_mode
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        if (old_state := await self.async_get_last_state()) is not None:
            if old_state.state in [mode.value for mode in HVACMode]:
                self._attr_hvac_mode = old_state.state
            if old_state.attributes is not None:
                if old_state.attributes.get(ATTR_HVAC_ACTION) in [
                    mode.value for mode in HVACAction
                ]:
                    self._attr_hvac_action = old_state.attributes[ATTR_HVAC_ACTION]
                if old_state.attributes.get(ATTR_TEMPERATURE) is not None:
                    self._attr_target_temperature = float(
                        old_state.attributes[ATTR_TEMPERATURE]
                    )
                if old_state.attributes.get(ATTR_CURRENT_TEMPERATURE) is not None:
                    self._attr_current_temperature = float(
                        old_state.attributes[ATTR_CURRENT_TEMPERATURE]
                    )
