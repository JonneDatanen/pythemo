"""Module containing the Device class to represent a Themo device and its state."""

from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from pythemo.client import ThemoClient


class Device:
    """A class to represent a Themo device and manage its state and attributes."""

    STATE_ATTRIBUTES: ClassVar[dict[str, str]] = {
        "floor_temperature": "FloorT",
        "info": "Info",
        "lights": "Lights",
        "manual_temperature": "MT",
        "max_power": "MP",
        "mode": "Mode",
        "power": "Power",
        "room_temperature": "RT",
        "sw_version": "SW",
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

        self.active_schedule: str | None = None
        self.available_schedules: list[str] = []

        self.floor_temperature: float | None = None
        self.info: str | None = None
        self.lights: bool | None = None
        self.manual_temperature: float | None = None
        self.max_power: float | None = None
        self.mode: str | None = None
        self.power: float | None = None
        self.room_temperature: float | None = None

    def __repr__(self) -> str:
        """Return a string representation of the Device instance."""
        return f"<Themo(id={self.id!r}, name={self.name!r}>"

    def update_attributes(self, data: dict[str, Any]) -> None:
        """Update device attributes."""
        self.name = data.get("Name")
        self.device_id = data.get("DeviceId")

        state_data: dict[str, Any] = data.get("State", {})
        self._update_state_attributes(state_data)

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
        for schedule in schedules_data:
            if schedule["Active"]:
                self.active_schedule = schedule["Name"]

    def _update_state_attributes(self, state_data: dict[str, Any]) -> None:
        """Update device state attributes."""
        for attr, key in self.STATE_ATTRIBUTES.items():
            value = state_data.get(key)
            if attr == "lights":
                value = bool(value)
            setattr(self, attr, value)

    async def set_lights(self, state: bool) -> None:
        """Set the lights state."""
        await self._client.set_device_lights(
            self.environment_id,
            self.id,
            state,
        )
        self.lights = state

    async def set_manual_temperature(self, temperature: int) -> None:
        """Set the manual temperature."""
        await self._client.set_device_temperature(
            self.environment_id,
            self.id,
            temperature,
        )
        self.manual_temperature = temperature

    async def set_mode(self, mode: str) -> None:
        """Set the device mode."""
        await self._client.set_device_mode(
            self.environment_id,
            self.id,
            mode,
        )
        self.mode = mode

    async def set_active_schedule(self, schedule_name: str) -> None:
        """Switch to a different schedule."""
        if schedule_name not in self.available_schedules:
            msg = f"Invalid schedule name: {schedule_name}"
            raise ValueError(msg)

        # Find the schedule ID for the given name
        schedules = await self._client.get_device_schedules(
            self.environment_id,
            self.id,
        )

        schedule_id = None
        for schedule in schedules:
            if schedule["Name"] == schedule_name:
                schedule_id = schedule["Id"]
                break

        if not schedule_id:
            msg = f"Could not find ID for schedule: {schedule_name}"
            raise ValueError(msg)

        # Update the schedule to be active
        await self._client.update_schedule(
            self.environment_id,
            self.id,
            schedule_id,
            schedule_name,
        )

        self.active_schedule = schedule_name
