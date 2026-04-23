# `pythemo` - Python Themo API Client

The `pythemo` repository provides a Python client for interacting with the Themo API. This library allows you to authenticate, fetch, and control devices associated with your Themo account.

## Features

- **Authentication**: Authenticate with the Themo API using your username and password.
- **Device Information**: Fetch all devices associated with your account.
- **Control Devices**: Control device attributes like lights, temperature, mode, and schedules.

## File Descriptions

### models.py

The `models.py` file contains the `Device` class which represents a Themo device. This class provides:

- Initialization of the device with its ID and token.
- Methods to fetch and update the device state and attributes.
- Methods to control the device, including setting lights, temperature, mode, and schedules.

### client.py

The `client.py` file contains the `ThemoClient` class which is responsible for:

- Authenticating the user and obtaining the access token.
- Fetching the client ID.
- Fetching all devices associated with the user's account.
- Closing the client session.

## Usage

To use this library, you need to:

1. Create an instance of the `ThemoClient` class using your Themo account credentials (username and password).
2. Call the `authenticate()` method to obtain the access token.
3. Fetch devices using the `get_all_devices()` method.
4. For each device, you can fetch and update its state, control its attributes, and manage its schedules using methods provided in the `Device` class.

## Dependencies

- `httpx`: A fully featured HTTP client for Python 3.

## Testing

The project includes integration tests for the client in `tests/test_client.py`.
These tests call the real Themo API (no mocks). You can run them with either a bearer token or username/password credentials.

### Install test dependencies

```powershell
python -m pip install -U pytest httpx
```

### Set environment variables

You can authenticate test requests in either of these ways:
- Bearer token (`THEMO_TOKEN`) for read-only API calls
- Username/password (`THEMO_USERNAME`, `THEMO_PASSWORD`) for the `authenticate()` integration test

PowerShell (Windows):

Bearer token (for token-based tests):

```powershell
$env:THEMO_TOKEN = "YOUR_BEARER_TOKEN"
```

Username/password (for `authenticate()` test):

```powershell
$env:THEMO_USERNAME = "your-email@example.com"
$env:THEMO_PASSWORD = "your-password"
```

Optional (enables device-specific tests):

```powershell
$env:THEMO_ENV_ID = "123"
$env:THEMO_DEVICE_ID = "456"
```

Git Bash:

Bearer token (for token-based tests):

```bash
export THEMO_TOKEN="YOUR_BEARER_TOKEN"
```

Username/password (for `authenticate()` test):

```bash
export THEMO_USERNAME="your-email@example.com"
export THEMO_PASSWORD="your-password"
```

Optional (enables device-specific tests):

```bash
export THEMO_ENV_ID="123"
export THEMO_DEVICE_ID="456"
```

### Run tests

Use `python -m pytest` instead of `pytest` on Windows to avoid PATH / interpreter mismatch issues.

PowerShell:

```powershell
python -m pytest -q tests\\test_client.py -s
```

Git Bash:

```bash
python -m pytest -q tests/test_client.py -s
```

Notes:
- If `THEMO_TOKEN` is not set, token-based integration tests will be skipped.
- If `THEMO_USERNAME` and `THEMO_PASSWORD` are not set, the `authenticate()` integration test will be skipped.
- If `THEMO_ENV_ID` and `THEMO_DEVICE_ID` are not set, device-specific integration tests will be skipped.
- Current integration tests are read-only and do not send control commands.


## Contributions

Contributions to the `pythemo` repository are welcome. Please ensure that you follow the coding conventions and write tests for any new features or changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
