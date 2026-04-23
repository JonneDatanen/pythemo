"""Module containing device models for Themo API payloads."""

from enum import IntEnum
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from pythemo.client import ThemoClient


class LockState(IntEnum):
    """Lock state values returned by the Themo API."""

    OFF = 0
    ON = 1
    HARD_LOCK = 2


class LocationResponse:
    """Represents top-level device location payload."""

    ATTRIBUTES: ClassVar[dict[str, str]] = {
        "country_short": "CountryShort",
        "lat": "Lat",
        "lng": "Lng",
        "raw_offset": "RawOffset",
        "weather_group_id": "WeatherGroupId",
    }

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self.country_short: str | None = None
        self.lat: float | None = None
        self.lng: float | None = None
        self.raw_offset: int | None = None
        self.weather_group_id: int | None = None
        self.update_attributes(data or {})

    def update_attributes(self, data: dict[str, Any]) -> None:
        """Update location attributes from API payload."""
        for attr, key in self.ATTRIBUTES.items():
            setattr(self, attr, data.get(key))


class DeviceParameters:
    """Represents nested device parameter flags in state."""

    ATTRIBUTES: ClassVar[dict[str, str]] = {
        "is_price_switch": "IsPriceSwitch",
        "is_air": "IsAir",
        "is_floor": "IsFloor",
        "is_combi": "IsCombi",
    }

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self.is_price_switch: bool | None = None
        self.is_air: bool | None = None
        self.is_floor: bool | None = None
        self.is_combi: bool | None = None
        self.update_attributes(data or {})

    def update_attributes(self, data: dict[str, Any]) -> None:
        """Update device parameter attributes from API payload."""
        for attr, key in self.ATTRIBUTES.items():
            value = data.get(key)
            if value is not None:
                value = bool(value)
            setattr(self, attr, value)


class DeviceState:
    """Represents the nested device state payload."""

    BOOLEAN_INT_ATTRIBUTES: ClassVar[set[str]] = {"frost_protection", "lights"}

    ATTRIBUTES: ClassVar[dict[str, str]] = {
        "connection_state": "CS",
        "device_parameters": "DeviceParameters",
        "floor_temperature": "FloorT",
        "frost_protection": "FTS",
        "frost_temperature": "FT",
        "info": "Info",
        "is_external_temp_ok": "IsExternalTempOk",
        "load_state": "LS",
        "lights": "Lights",
        "lock": "Lock",
        "manual_temperature": "MT",
        "max_power": "MP",
        "mode": "Mode",
        "outside_temperature": "OT",
        "power": "Power",
        "room_temperature": "RT",
        "state_time": "Time",
        "temperature_sensor": "TmpSns",
        "timer_boost": "TB",
        "failsafe_temperature": "ST",
        "sw_version": "SW",
    }

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self.connection_state: bool | None = None
        self.device_parameters: DeviceParameters | None = None
        self.floor_temperature: float | None = None
        self.frost_protection: bool | None = None
        self.frost_temperature: float | None = None
        self.info: float | None = None
        self.is_external_temp_ok: bool | None = None
        self.load_state: int | None = None
        self.lights: bool | None = None
        self.lock: LockState | int | None = None
        self.manual_temperature: float | None = None
        self.max_power: float | None = None
        self.mode: str | None = None
        self.outside_temperature: float | None = None
        self.power: bool | None = None
        self.room_temperature: float | None = None
        self.state_time: str | None = None
        self.temperature_sensor: str | None = None
        self.timer_boost: int | None = None
        self.failsafe_temperature: float | None = None
        self.sw_version: str | None = None
        self.update_attributes(data or {})

    def update_attributes(self, data: dict[str, Any]) -> None:
        """Update state attributes from API payload."""
        for attr, key in self.ATTRIBUTES.items():
            value = data.get(key)
            if attr in self.BOOLEAN_INT_ATTRIBUTES and value is not None:
                value = bool(value)
            if attr == "lock" and value is not None:
                try:
                    value = LockState(value)
                except ValueError:
                    pass
            if attr == "device_parameters" and isinstance(value, dict):
                if self.device_parameters is None:
                    self.device_parameters = DeviceParameters(value)
                else:
                    self.device_parameters.update_attributes(value)
                value = self.device_parameters
            elif attr == "device_parameters":
                value = None
            setattr(self, attr, value)


class Device:
    """Represents a Themo device with top-level metadata and nested state."""

    ATTRIBUTES: ClassVar[dict[str, str]] = {
        "id": "Id",
        "name": "Name",
        "device_id": "DeviceId",
        "device_auth": "DeviceAuth",
        "client_id": "ClientId",
        "location": "Location",
        "environment_id": "EnvironmentId",
        "environment_name": "EnvironmentName",
        "tags": "Tags",
        "active_schedule_id": "ActiveScheduleId",
        "temperature_schedule": "TemperatureSchedule",
        "sw_version": "SW",
        "state": "State",
    }

    def __init__(
        self,
        device_id: str,
        environment_id: str,
        client: "ThemoClient",
    ) -> None:
        """Initialize a Device instance."""
        self.id: str = device_id
        self.environment_id: str = environment_id
        self._client = client

        self.name: str | None = None
        self.device_id: str | None = None
        self.device_auth: str | None = None
        self.client_id: int | None = None
        self.location: LocationResponse | None = None
        self.environment_name: str | None = None
        self.tags: str | None = None
        self.active_schedule_id: int | None = None
        self.temperature_schedule: str | None = None
        self.sw_version: str | None = None

        self.active_schedule: str | None = None
        self.available_schedules: list[str] = []

        self.state: DeviceState = DeviceState()

    def __repr__(self) -> str:
        """Return a string representation of the Device instance."""
        return f"<Themo(id={self.id!r}, name={self.name!r})>"

    def update_attributes(self, data: dict[str, Any]) -> None:
        """Update top-level device attributes and nested state."""
        for attr, key in self.ATTRIBUTES.items():
            value = data.get(key)

            if attr in {"id", "environment_id"} and value is not None:
                value = str(value)

            if attr == "location" and isinstance(value, dict):
                if self.location is None:
                    self.location = LocationResponse(value)
                else:
                    self.location.update_attributes(value)
                value = self.location
            elif attr == "location":
                value = None

            if attr == "state" and isinstance(value, dict):
                self.state.update_attributes(value)
                value = self.state
            elif attr == "state":
                value = self.state

            setattr(self, attr, value)

    async def update_state(self) -> None:
        """Primary method to update the device state."""
        await self.fetch_data()
        await self.fetch_schedules()

    async def fetch_data(self) -> dict[str, Any]:
        """Fetch and set the initial data for the device."""
        device_data = await self._client.get_device_data(
            self.environment_id,
            self.id,
        )
        self.update_attributes(device_data)
        return device_data

    async def fetch_current_state(self) -> None:
        """Update only the current state of the device."""
        await self.fetch_data()

    async def fetch_schedules(self) -> None:
        """Fetch and update device schedules."""
        schedules_data = await self._client.get_device_schedules(
            self.environment_id,
            self.id,
        )
        self._update_schedules(schedules_data)

    def _update_schedules(self, schedules_data: list[dict[str, Any]]) -> None:
        """Update device schedules based on the provided data."""
        self.available_schedules = [schedule["Name"] for schedule in schedules_data]
        self.active_schedule = None
        for schedule in schedules_data:
            if schedule["Active"]:
                self.active_schedule = schedule["Name"]

    async def set_lights(self, state: bool) -> None:
        """Set the lights state."""
        await self._client.set_device_lights(
            self.environment_id,
            self.id,
            state,
        )
        self.state.lights = state

    async def set_manual_temperature(self, temperature: int) -> None:
        """Set the manual temperature."""
        await self._client.set_device_temperature(
            self.environment_id,
            self.id,
            temperature,
        )
        self.state.manual_temperature = temperature

    async def set_mode(self, mode: str) -> None:
        """Set the device mode."""
        await self._client.set_device_mode(
            self.environment_id,
            self.id,
            mode,
        )
        self.state.mode = mode

    async def set_active_schedule(self, schedule_name: str) -> None:
        """Switch to a different schedule."""
        if schedule_name not in self.available_schedules:
            msg = f"Invalid schedule name: {schedule_name}"
            raise ValueError(msg)

        schedules = await self._client.get_device_schedules(
            self.environment_id,
            self.id,
        )

        schedule_id = None
        for schedule in schedules:
            if schedule["Name"] == schedule_name:
                schedule_id = schedule["Id"]
                break

        if schedule_id is None:
            msg = f"Could not find ID for schedule: {schedule_name}"
            raise ValueError(msg)

        await self._client.update_schedule(
            self.environment_id,
            self.id,
            schedule_id,
            schedule_name,
        )

        self.active_schedule = schedule_name
