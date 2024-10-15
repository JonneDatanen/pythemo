"""Module containing the Device class to represent a Themo device and manage its state. and attributes."""

import json
from typing import Any

import httpx

from .constants import BASE_URL


class Device:
    """A class to represent a Themo device and manage its state and attributes."""

    STATE_ATTRIBUTES: dict[str, str] = {
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

    def __init__(self, id: str, client) -> None:
        """Initialize a Device instance."""
        self.id: str = id
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

    async def _api_request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Make API requests."""
        url: str = f"{BASE_URL}/{endpoint}"
        response: httpx.Response = await getattr(self._client, method)(url, **kwargs)
        response.raise_for_status()
        try:
            return response.json()
        except json.JSONDecodeError:
            pass

    def _update_attributes(self, data: dict[str, Any]) -> None:
        """Update device attributes."""
        self.name = data.get("DeviceName")
        self.device_id = data.get("DeviceID")

        state_data: dict[str, Any] = data.get("State", {})
        self._update_state_attributes(state_data)

    async def update_state(self):
        """Primary method to update the device state."""
        if not self.is_initialized():
            await self.fetch_initial_data()
        else:
            await self.fetch_current_state()
        await self.fetch_schedules()

    def is_initialized(self) -> bool:
        """Determine if the device has been initialized."""
        return self.device_id is not None

    async def fetch_initial_data(self):
        """Fetch and set the initial data for the device."""
        device_data = await self._get_device_data()
        self._update_attributes(device_data)

    async def fetch_current_state(self):
        """Update only the current state of the device."""
        state_data = await self._get_state_data()
        self._update_state_attributes(state_data)

    async def fetch_schedules(self):
        """Fetch and update device schedules."""
        schedules_data = await self._get_schedules_data()
        self._update_schedules(schedules_data)

    def _update_schedules(self, schedules_data: list[dict[str, Any]]) -> None:
        """Update device schedules based on the provided data."""
        self.available_schedules = [schedule["Name"] for schedule in schedules_data]
        for schedule in schedules_data:
            if schedule["Active"]:
                self.active_schedule = schedule["Name"]

    async def _get_device_data(self) -> dict[str, Any]:
        return await self._api_request("get", f"api/devices/{self.id}")

    async def _get_state_data(self) -> dict[str, Any]:
        return await self._api_request("get", f"api/devices/{self.id}/state")

    async def _get_schedules_data(self) -> list[dict[str, Any]]:
        params = {"api-version": "2.0"}
        return await self._api_request(
            "get", f"api/devices/{self.id}/schedules/temperature", params=params
        )

    def _update_state_attributes(self, state_data):
        for attr, key in self.STATE_ATTRIBUTES.items():
            value = state_data.get(key)
            if attr == "lights":
                value = bool(value)
            setattr(self, attr, value)

    async def set_lights(self, state: bool) -> None:
        """Set the lights state."""
        payload: dict[str, str] = {"CLights": "1" if state else "0"}
        await self._api_request(
            "post", f"Api/Devices/{self.id}/Message/Lights", json=payload
        )
        self.lights = state

    async def set_manual_temperature(self, temperature: int) -> None:
        """Set the lights state."""
        payload: dict[str, str] = {"CMT": str(temperature)}
        await self._api_request(
            "post", f"Api/Devices/{self.id}/Message/Temperature", json=payload
        )
        self.manual_temperature = temperature

    async def update_schedules(self) -> None:
        """Fetch and update the device schedules."""
        params: dict[str, str] = {"api-version": "2.0"}
        data: list[dict[str, Any]] = await self._api_request(
            "get", f"api/devices/{self.id}/schedules/temperature", params=params
        )
        self.available_schedules = [schedule["Name"] for schedule in data]
        for schedule in data:
            if schedule["Active"]:
                self.active_schedule = schedule["Name"]

    async def set_active_schedule(self, schedule_name: str) -> None:
        """Switch to a different schedule."""
        if schedule_name not in self.available_schedules:
            raise ValueError(f"Invalid schedule name: {schedule_name}")

        await self._api_request(
            "put",
            (
                f"api/devices/{self.id}/schedules/temperature/switch?"
                f"scheduleName={schedule_name.replace(' ', '+')}&api-version=2.0"
            ),
        )
        self.active_schedule = schedule_name

    async def set_mode(self, mode: str) -> None:
        """Switch to a different schedule."""
        if mode not in ("Manual", "Off", "SLS"):
            raise ValueError

        payload: dict[str, str] = {"CMode": mode}
        await self._api_request(
            "post",
            f"api/devices/{self.id}/message/mode",
            json=payload,
        )
        self.mode = mode
