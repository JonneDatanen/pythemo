import asyncio
import os

import httpx
import pytest

from pythemo.client import ThemoClient


def _run(coro):
    return asyncio.run(coro)


def _env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        pytest.skip(f"Missing environment variable: {name}")
    return value


def _token() -> str:
    return _env("THEMO_TOKEN")


def test_integration_get_environments() -> None:
    async def _test() -> None:
        http_client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {_token()}"},
            timeout=30.0,
        )
        client = ThemoClient(username="", password="", client=http_client)
        try:
            environments = await client.get_environments()
            assert isinstance(environments, list)
            assert environments, "No environments returned"
            assert all("Id" in env for env in environments)
        finally:
            await http_client.aclose()

    _run(_test())


def test_integration_get_all_devices() -> None:
    async def _test() -> None:
        http_client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {_token()}"},
            timeout=30.0,
        )
        client = ThemoClient(username="", password="", client=http_client)
        try:
            devices = await client.get_all_devices()
            assert isinstance(devices, list)
            assert devices, "No devices returned"

            device = devices[0]
            assert device.id
            assert device.environment_id
            assert hasattr(device, "state")
            assert device.state is not None
            assert hasattr(device.state, "ATTRIBUTES")

            # Ensure all mapped state attrs exist on the DeviceState instance
            for attr in device.state.ATTRIBUTES:
                assert hasattr(device.state, attr), f"Missing mapped state attribute: {attr}"
        finally:
            await http_client.aclose()

    _run(_test())


def test_integration_get_specific_device_data() -> None:
    env_id = os.getenv("THEMO_ENV_ID")
    device_id = os.getenv("THEMO_DEVICE_ID")
    if not env_id or not device_id:
        pytest.skip("Set THEMO_ENV_ID and THEMO_DEVICE_ID to run this test")

    async def _test() -> None:
        http_client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {_token()}"},
            timeout=30.0,
        )
        client = ThemoClient(username="", password="", client=http_client)
        try:
            payload = await client.get_device_data(env_id, device_id)
            assert isinstance(payload, dict)
            assert str(payload.get("Id")) == str(device_id)
            assert "State" in payload
            assert isinstance(payload["State"], dict)
        finally:
            await http_client.aclose()

    _run(_test())


def test_integration_get_device_model_and_schedules() -> None:
    env_id = os.getenv("THEMO_ENV_ID")
    device_id = os.getenv("THEMO_DEVICE_ID")
    if not env_id or not device_id:
        pytest.skip("Set THEMO_ENV_ID and THEMO_DEVICE_ID to run this test")

    async def _test() -> None:
        http_client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {_token()}"},
            timeout=30.0,
        )
        client = ThemoClient(username="", password="", client=http_client)
        try:
            device = await client.get_device(env_id, device_id)
            assert device.id == str(device_id)
            assert device.environment_id == str(env_id)
            assert isinstance(device.available_schedules, list)
            assert device.state is not None
        finally:
            await http_client.aclose()

    _run(_test())


def test_integration_device_state_mapping_matches_raw_payload() -> None:
    env_id = os.getenv("THEMO_ENV_ID")
    device_id = os.getenv("THEMO_DEVICE_ID")
    if not env_id or not device_id:
        pytest.skip("Set THEMO_ENV_ID and THEMO_DEVICE_ID to run this test")

    async def _test() -> None:
        http_client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {_token()}"},
            timeout=30.0,
        )
        client = ThemoClient(username="", password="", client=http_client)
        try:
            request_path = f"api/environments/{env_id}/devices/{device_id}"
            print("RAW REQUEST:", {"method": "GET", "path": request_path, "params": {"state": True}})

            raw_payload = await client.get_device_data(env_id, device_id)
            print("RAW RESPONSE:", raw_payload)

            device = await client.get_device(env_id, device_id)

            raw_state = raw_payload.get("State")
            assert isinstance(raw_state, dict), "Raw payload missing State dict"

            failures: list[str] = []

            def _log_check(label: str, expected: object, actual: object) -> bool:
                ok = actual == expected
                print(f"{'OK' if ok else 'FAIL'} {label}: expected={expected!r}, actual={actual!r}")
                return ok

            top_attr_map = device.ATTRIBUTES
            mapped_top_keys = set(top_attr_map.values())
            unmapped_top_keys = sorted(set(raw_payload) - mapped_top_keys)
            print(
                f"{'OK' if not unmapped_top_keys else 'FAIL'} top-level mapping coverage: "
                f"unmapped={unmapped_top_keys!r}",
            )
            if unmapped_top_keys:
                failures.append(f"Unmapped raw top-level keys: {unmapped_top_keys}")

            for attr, raw_key in top_attr_map.items():
                if attr == "state":
                    continue

                raw_value = raw_payload.get(raw_key)
                model_value = getattr(device, attr)

                if attr in {"id", "environment_id"} and raw_value is not None:
                    raw_value = str(raw_value)

                if attr == "location":
                    if raw_value is None:
                        if not _log_check("device.location", None, model_value):
                            failures.append(f"device.location: expected None, got {model_value!r}")
                        continue

                    raw_is_dict = isinstance(raw_value, dict)
                    print(
                        f"{'OK' if raw_is_dict else 'FAIL'} device.location raw type: "
                        f"expected=dict, actual={type(raw_value).__name__}",
                    )
                    if not raw_is_dict:
                        failures.append("Top-level Location must be dict when present")
                        continue
                    if not _log_check("device.location present", True, model_value is not None):
                        failures.append("Mapped location model missing")
                        continue

                    location_attr_map = model_value.ATTRIBUTES
                    mapped_location_keys = set(location_attr_map.values())
                    unmapped_location_keys = sorted(set(raw_value) - mapped_location_keys)
                    print(
                        f"{'OK' if not unmapped_location_keys else 'FAIL'} location mapping coverage: "
                        f"unmapped={unmapped_location_keys!r}",
                    )
                    if unmapped_location_keys:
                        failures.append(f"Unmapped Location keys: {unmapped_location_keys}")

                    for location_attr, location_raw_key in location_attr_map.items():
                        expected_loc = raw_value.get(location_raw_key)
                        actual_loc = getattr(model_value, location_attr)
                        if not _log_check(
                            f"device.location.{location_attr}",
                            expected_loc,
                            actual_loc,
                        ):
                            failures.append(
                                f"device.location.{location_attr}: expected {expected_loc!r}, got {actual_loc!r}",
                            )
                    continue

                if not _log_check(f"device.{attr}", raw_value, model_value):
                    failures.append(f"device.{attr}: expected {raw_value!r}, got {model_value!r}")

            state_attr_map = device.state.ATTRIBUTES
            mapped_raw_keys = set(state_attr_map.values())
            unmapped_state_keys = sorted(set(raw_state) - mapped_raw_keys)
            print(
                f"{'OK' if not unmapped_state_keys else 'FAIL'} state mapping coverage: "
                f"unmapped={unmapped_state_keys!r}",
            )
            if unmapped_state_keys:
                failures.append(f"Unmapped raw State keys: {unmapped_state_keys}")

            for attr, raw_key in state_attr_map.items():
                raw_value = raw_state.get(raw_key)
                model_value = getattr(device.state, attr)

                if attr == "device_parameters":
                    if raw_value is None:
                        if not _log_check("state.device_parameters", None, model_value):
                            failures.append(
                                f"state.device_parameters: expected None, got {model_value!r}",
                            )
                        continue

                    raw_is_dict = isinstance(raw_value, dict)
                    print(
                        f"{'OK' if raw_is_dict else 'FAIL'} state.device_parameters raw type: "
                        f"expected=dict, actual={type(raw_value).__name__}",
                    )
                    if not raw_is_dict:
                        failures.append("State.DeviceParameters must be a dict when present")
                        continue
                    if not _log_check("state.device_parameters present", True, model_value is not None):
                        failures.append("Mapped device_parameters model missing")
                        continue

                    param_attr_map = model_value.ATTRIBUTES
                    mapped_param_keys = set(param_attr_map.values())
                    unmapped_param_keys = sorted(set(raw_value) - mapped_param_keys)
                    print(
                        f"{'OK' if not unmapped_param_keys else 'FAIL'} device_parameters mapping coverage: "
                        f"unmapped={unmapped_param_keys!r}",
                    )
                    if unmapped_param_keys:
                        failures.append(f"Unmapped DeviceParameters keys: {unmapped_param_keys}")

                    for param_attr, param_raw_key in param_attr_map.items():
                        expected_param_value = raw_value.get(param_raw_key)
                        if expected_param_value is not None:
                            expected_param_value = bool(expected_param_value)
                        actual_param_value = getattr(model_value, param_attr)
                        if not _log_check(
                            f"state.device_parameters.{param_attr}",
                            expected_param_value,
                            actual_param_value,
                        ):
                            failures.append(
                                f"state.device_parameters.{param_attr}: expected {expected_param_value!r}, got {actual_param_value!r}",
                            )
                    continue

                if attr in device.state.BOOLEAN_INT_ATTRIBUTES and raw_value is not None:
                    expected_bool = bool(raw_value)
                    if not _log_check(f"state.{attr}", expected_bool, model_value):
                        failures.append(f"state.{attr}: expected {expected_bool!r}, got {model_value!r}")
                    is_bool = isinstance(model_value, bool)
                    print(
                        f"{'OK' if is_bool else 'FAIL'} state.{attr} type: "
                        f"expected=bool, actual={type(model_value).__name__}",
                    )
                    if not is_bool:
                        failures.append(
                            f"state.{attr} type mismatch: expected bool, got {type(model_value).__name__}",
                        )
                    continue

                if not _log_check(f"state.{attr}", raw_value, model_value):
                    failures.append(f"state.{attr}: expected {raw_value!r}, got {model_value!r}")

            assert not failures, "Device mapping mismatches:\n" + "\n".join(failures)
        finally:
            await http_client.aclose()

    _run(_test())


def test_integration_authenticate_with_username_password() -> None:
    username = os.getenv("THEMO_USERNAME")
    password = os.getenv("THEMO_PASSWORD")
    if not username or not password:
        pytest.skip("Set THEMO_USERNAME and THEMO_PASSWORD to run this test")

    async def _test() -> None:
        http_client = httpx.AsyncClient(timeout=30.0)
        client = ThemoClient(username=username, password=password, client=http_client)
        try:
            await client.authenticate()
            auth_header = http_client.headers.get("Authorization", "")
            assert auth_header.startswith("Bearer ")
            assert client._environments is not None
            assert isinstance(client._environments, list)
        finally:
            await http_client.aclose()

    _run(_test())


