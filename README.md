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

## Contributions

Contributions to the `pythemo` repository are welcome. Please ensure that you follow the coding conventions and write tests for any new features or changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
