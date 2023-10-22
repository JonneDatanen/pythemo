import json
from typing import Any, Dict, List, Optional

import httpx

from pythemo.constants import BASE_URL


class Device:
    STATE_ATTRIBUTES: Dict[str, str] = {
        "floor_temperature": "FloorT",
        "info": "Info",
        "lights": "Lights",
        "manual_temperature": "MT",
        "max_power": "MP",
        "mode": "Mode",
        "power": "Power",
        "room_temperature": "RT",
    }

    def __init__(self, id: str, token: str) -> None:
        """Initialize a Device instance."""
        self.id: str = id
        self.token: str = token
        self._client: httpx.AsyncClient = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        self.name: Optional[str] = None
        self.device_id: Optional[str] = None

        self.active_schedule: Optional[str] = None
        self.available_schedules: List[str] = []

        self.floor_temperature: Optional[float] = None
        self.info: Optional[str] = None
        self.lights: Optional[bool] = None
        self.manual_temperature: Optional[float] = None
        self.max_power: Optional[float] = None
        self.mode: Optional[str] = None
        self.power: Optional[float] = None
        self.room_temperature: Optional[float] = None

    def __repr__(self) -> str:
        """Return a string representation of the Device instance."""
        return f"<Themo(id={self.id!r}, name={self.name!r}>"

    async def _api_request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """Helper method to make API requests."""
        url: str = f"{BASE_URL}/{endpoint}"
        response: httpx.Response = await getattr(self._client, method)(url, **kwargs)
        response.raise_for_status()
        try:
            return response.json()
        except json.JSONDecodeError:
            pass

    def _update_attributes(self, data: Dict[str, Any]) -> None:
        """Helper method to update device attributes."""
        self.name = data.get("DeviceName")
        self.device_id = data.get("DeviceID")

        state_data: Dict[str, Any] = data.get("State", {})
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

    def _update_schedules(self, schedules_data: List[Dict[str, Any]]) -> None:
        """Helper method to update device schedules based on the provided data."""
        self.available_schedules = [schedule["Name"] for schedule in schedules_data]
        for schedule in schedules_data:
            if schedule["Active"]:
                self.active_schedule = schedule["Name"]

    async def _get_device_data(self) -> Dict[str, Any]:
        return await self._api_request("get", f"api/devices/{self.id}")

    async def _get_state_data(self) -> Dict[str, Any]:
        return await self._api_request("get", f"api/devices/{self.id}/state")

    async def _get_schedules_data(self) -> List[Dict[str, Any]]:
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
        payload: Dict[str, str] = {"CLights": "1" if state else "0"}
        await self._api_request(
            "post", f"Api/Devices/{self.id}/Message/Lights", json=payload
        )
        self.lights = state

    async def set_manual_temperature(self, temperature: int) -> None:
        """Set the lights state."""
        payload: Dict[str, str] = {"CMT": str(temperature)}
        await self._api_request(
            "post", f"Api/Devices/{self.id}/Message/Temperature", json=payload
        )
        self.manual_temperature = temperature

    async def update_schedules(self) -> None:
        params: Dict[str, str] = {"api-version": "2.0"}
        data: List[Dict[str, Any]] = await self._api_request(
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

        payload: Dict[str, str] = {"CMode": mode}
        await self._api_request(
            "post",
            f"api/devices/{self.id}/message/mode",
            json=payload,
        )
        self.mode = mode
