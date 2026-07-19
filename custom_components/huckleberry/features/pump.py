"""Pump-related entities for Huckleberry."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

from .. import HuckleberryDataUpdateCoordinator
from ..entity import HuckleberryBaseEntity
from ..models import HuckleberryChildProfile
from ..timestamps import as_datetime, as_iso8601_datetime, as_iso8601_duration


def build_pump_sensors(
    coordinator: HuckleberryDataUpdateCoordinator,
    children: list[HuckleberryChildProfile],
) -> list[SensorEntity]:
    """Build pump-related sensors."""
    return [HuckleberryPumpSensor(coordinator, child) for child in children]


class HuckleberryPumpSensor(HuckleberryBaseEntity, SensorEntity):
    """Sensor showing last pumping session information."""

    _attr_icon = "mdi:cup-water"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_name = "Pumping"

    def __init__(self, coordinator: HuckleberryDataUpdateCoordinator, child: HuckleberryChildProfile) -> None:
        super().__init__(coordinator, child)
        self._attr_unique_id = f"{self.child_uid}_pump"

    def _last_pump(self):
        pump_status = self.coordinator.get_pump_status(self.child_uid)
        prefs = pump_status.prefs if pump_status is not None else None
        return prefs.lastPump if prefs is not None else None

    @property
    def native_value(self):
        """Return the last pump session timestamp."""
        last_pump = self._last_pump()
        return as_datetime(last_pump.start if last_pump is not None else None)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return pump session attributes."""
        last_pump = self._last_pump()
        if last_pump is None:
            return {}

        attributes: dict[str, object] = {}
        if last_pump.start is not None:
            attributes["time"] = as_iso8601_datetime(last_pump.start)

        left = last_pump.leftAmount
        right = last_pump.rightAmount
        if left is not None or right is not None:
            attributes["left_amount"] = left
            attributes["right_amount"] = right
            attributes["amount"] = (left or 0) + (right or 0)
        if last_pump.units is not None:
            attributes["units"] = last_pump.units
        if last_pump.duration is not None:
            attributes["duration"] = as_iso8601_duration(last_pump.duration)

        return attributes
