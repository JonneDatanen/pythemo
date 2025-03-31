"""Module containing the Client class for interacting with Themo API."""

from typing import Any, cast

import httpx

from pythemo.models import Device
from pythemo.utils import request


class ThemoAuthenticationError(Exception):
    """Exception raised for errors in the authentication process."""

    def __init__(self, message: str, response: httpx.Response | None = None) -> None:
        """Initialize the error with a message and response."""
        self.message = message
        self.response = response
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return a string representation of the error."""
        if self.response:
            return f"{self.message} (status code: {self.response.status_code})"
        return self.message


class ThemoConnectionError(Exception):
    """Exception raised for connection errors."""

    def __init__(self, message: str, response: httpx.Response | None = None) -> None:
        """Initialize the error with a message and optional response."""
        self.message = message
        self.response = response
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return a string representation of the error."""
        if self.response:
            return f"{self.message} (status code: {self.response.status_code})"
        return self.message


class ThemoClient:
    """A class to represent a client for interacting with Themo API."""

    def __init__(
        self,
        username: str,
        password: str,
        client: httpx.AsyncClient | None = None,  # Add support for custom client
    ) -> None:
        """Initialize a Client instance.

        Args:
            username: The username for authentication
            password: The password for authentication
            client: Optional custom httpx AsyncClient instance

        """
        self._client = client if client is not None else httpx.AsyncClient()
        self._environments: list[dict[str, Any]] = []
        self.username = username
        self.password = password

    async def authenticate(self) -> None:
        """Authenticate with the Themo API using the credentials."""
        try:
            # Perform login to get token
            login_response = await request(
                self._client,
                "post",
                "api/auth/login",
                json={
                    "Username": self.username,
                    "Password": self.password,
                },
            )
        except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            # Handle all timeout errors the same way
            msg = f"Connection timeout while connecting to the API: {e}"
            raise ThemoConnectionError(msg) from e
        except httpx.HTTPError as e:
            # General HTTP error handling
            msg = "Authentication failed"
            raise ThemoAuthenticationError(msg) from e
        except Exception as e:
            # Catch-all for other errors
            msg = f"Unexpected error during authentication: {e}"
            raise ThemoConnectionError(msg) from e

        # Extract token
        token = login_response.get("Token")
        if not token:
            msg = "Authentication failed: No token received"
            raise ThemoAuthenticationError(msg)

        # Add the token to the client headers
        self._client.headers.update({"Authorization": f"Bearer {token}"})

        # Get environments
        await self.get_environments()

    # Environment operations
    async def get_environments(self) -> list[dict[str, Any]]:
        """Get all environments for the authenticated user."""
        self._environments = cast(
            "list[dict[str, Any]]",
            await request(self._client, "get", "api/environments"),
        )
        return self._environments

    # Device discovery
    async def get_all_devices(self) -> list["Device"]:
        """Get all devices across all environments for the authenticated user."""
        # Make sure we have environments
        if not self._environments:
            await self.get_environments()

        devices = []

        # Then fetch devices for each environment
        for env in self._environments:
            env_id = env.get("Id")
            if env_id is None:
                continue
            env_devices = cast(
                "list[dict[str, Any]]",
                await request(
                    self._client,
                    "get",
                    f"api/environments/{env_id}/devices",
                    params={"state": True},
                ),
            )
            for device_data in env_devices:
                device_id = device_data.get("Id")
                if device_id is not None:
                    device = Device(str(device_id), str(env_id), self)
                    device.update_attributes(device_data)
                    devices.append(device)

        return devices

    async def get_device(
        self,
        environment_id: str,
        device_id: str,
    ) -> "Device":
        """Get a specific device by its environment ID and device ID."""
        device = Device(device_id, environment_id, self)
        await device.update_state()
        return device

    # Device operations API
    async def get_device_data(
        self,
        environment_id: str,
        device_id: str,
    ) -> dict[str, Any]:
        """Get device data with state information."""
        try:
            return await request(
                self._client,
                "get",
                f"api/environments/{environment_id}/devices/{device_id}",
                params={"state": True},  # Always request state data
            )
        except Exception as e:
            msg = "Failed to get device data"
            raise ThemoConnectionError(msg, response=None) from e

    async def get_device_schedules(
        self,
        environment_id: str,
        device_id: str,
    ) -> list[dict[str, Any]]:
        """Get device schedules.

        Returns an empty list on error or if no schedules are found.
        """
        return cast(
            "list[dict[str, Any]]",
            await request(
                self._client,
                "get",
                f"api/environments/{environment_id}/devices/{device_id}/schedules",
            ),
        )

    async def set_device_lights(
        self,
        environment_id: str,
        device_id: str,
        state: bool,
    ) -> None:
        """Set device lights state."""
        await request(
            self._client,
            "post",
            f"api/environments/{environment_id}/devices/{device_id}/commands/message",
            json={"CLights": 1 if state else 0},
        )

    async def set_device_temperature(
        self,
        environment_id: str,
        device_id: str,
        temperature: float,
    ) -> None:
        """Set device temperature."""
        await request(
            self._client,
            "post",
            f"api/environments/{environment_id}/devices/{device_id}/commands/message",
            json={"CMT": temperature},
        )

    async def set_device_mode(
        self,
        environment_id: str,
        device_id: str,
        mode: str,
    ) -> None:
        """Set device operation mode."""
        if mode not in ("Manual", "Off", "SLS"):
            msg = f"Invalid mode: {mode}"
            raise ValueError(msg)

        await request(
            self._client,
            "post",
            f"api/environments/{environment_id}/devices/{device_id}/commands/message",
            json={"CMode": mode},
        )

    async def update_schedule(
        self,
        environment_id: str,
        device_id: str,
        schedule_id: str,
        schedule_name: str,
    ) -> None:
        """Update a schedule to be active."""
        await request(
            self._client,
            "put",
            f"api/environments/{environment_id}/devices/{device_id}/schedules/{schedule_id}",
            json={
                "Name": schedule_name,
                "Active": True,
            },
        )
