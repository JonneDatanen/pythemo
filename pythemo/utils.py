"""Utility functions for the Pythemo library."""

import json
from typing import Any

import httpx

from pythemo.constants import API_VERSION, BASE_URL


async def request(
    client: httpx.AsyncClient,
    method: str,
    endpoint: str,
    **kwargs: dict,
) -> dict[str, Any]:
    """Make API requests to the Themo API.

    Args:
        client: HTTP client to use for the request
        method: HTTP method (get, post, put, etc.)
        endpoint: API endpoint path
        auth_token: Authentication token
        **kwargs: Additional arguments to pass to the request

    Returns:
        Parsed JSON response or empty dict

    """
    url: str = f"{BASE_URL}/{endpoint}"

    # Ensure api-version is included in params
    params = kwargs.pop("params", {}) | {"api-version": API_VERSION}

    # Set timeout if not provided
    timeout = kwargs.pop("timeout", 30)

    # Pass the request with all parameters
    response: httpx.Response = await getattr(client, method)(
        url,
        params=params,
        timeout=timeout,
        **kwargs,  # Pass through remaining kwargs (json, etc.)
    )

    response.raise_for_status()
    try:
        return response.json()
    except json.decoder.JSONDecodeError:
        return {}
