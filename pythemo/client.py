import httpx

from pythemo.constants import BASE_URL
from pythemo.models import Device


class ThemoClient:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.token = None
        self.client_id = None
        self._client = httpx.AsyncClient()

    async def authenticate(self):
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
        self.token = data["access_token"]

        self._client.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    async def get_client_id(self):
        response = await self._client.get(f"{BASE_URL}/api/clients/me")
        data = response.json()
        self.client_id = data.get("ID")

    async def get_all_devices(self):
        response = await self._client.get(f"{BASE_URL}/Api/Devices")
        devices_data = response.json()
        return [
            Device(id=item["ID"], token=self.token) for item in devices_data["Devices"]
        ]

    async def close(self):
        """Close the client session."""
        await self._client.aclose()
