"""Provides a client for interacting with the Themo API."""

import httpx

from .constants import BASE_URL
from .models import Device


class ThemoAuthenticationError(Exception):
    """Exception raised for errors in the authentication process."""

    def __init__(self, message: str, response: httpx.Response):
        self.message = message
        self.response = response
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} (status code: {self.response.status_code})"


class ThemoConnectionError(Exception):
    """Exception raised for connection errors."""

    def __init__(self, message: str, response: httpx.Response = None):
        self.message = message
        self.response = response
        super().__init__(self.message)

    def __str__(self):
        if self.response:
            return f"{self.message} (status code: {self.response.status_code})"
        return self.message


class ThemoClient:
    """Client for interacting with the Themo API."""

    def __init__(self, username, password, client=None) -> None:
        """Initialize the ThemoClient with username, password, and an optional HTTP client.

        :param username: The username for authentication.
        :param password: The password for authentication.
        :param client: An optional HTTP client instance.
        """
        self.username = username
        self.password = password
        self.token = None
        self.client_id = None
        self._client = client or httpx.AsyncClient()

    async def authenticate(self):
        """Authenticate the client and obtain an access token."""
        try:
            response = await self._client.post(
                f"{BASE_URL}/token",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "password",
                    "username": self.username,
                    "password": self.password,
                },
            )
            data = response.json()

            if response.status_code != 200:
                raise ThemoAuthenticationError(
                    data.get("error_description", "Unknown error"),
                    response,
                )

            self.token = data["access_token"]

            self._client.headers.update(
                {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
            )
        except httpx.RequestError as e:
            raise ThemoConnectionError("Failed to connect to Themo API") from e

    async def get_client_id(self):
        """Retrieve and set the client ID."""
        response = await self._client.get(f"{BASE_URL}/api/clients/me")
        data = response.json()
        self.client_id = data.get("ID")

    async def get_all_devices(self):
        """Retrieve all devices associated with the authenticated client.

        :return: A list of Device instances.
        """
        response = await self._client.get(f"{BASE_URL}/Api/Devices")
        devices_data = response.json()

        return [
            Device(id=item["ID"], client=self._client)
            for item in devices_data["Devices"]
        ]

    async def close(self):
        """Close the client session."""
        await self._client.aclose()
