from typing import Any

import httpx

from pythemo.constants import BASE_URL


def get_token(username: str, password: str) -> str:
    """
    Obtain an authentication token using the provided username and password.

    :param username: The username for authentication.
    :param password: The password for authentication.
    :return: The authentication token.
    :raises ValueError: If there's an error obtaining the token.
    """
    with httpx.Client() as client:
        response = client.post(
            f"{BASE_URL}/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "password",
                "username": username,
                "password": password,
            },
        )
        data: Any = response.json()

        if response.status_code == 200 and "access_token" in data:
            return data["access_token"]
        else:
            raise ValueError(f"Error obtaining token: {response.text}")
