# VSS for Home Assistant

Home Assistant integration for [Visionect Software Suite (VSS)](https://www.visionect.com/) e-paper displays.
It requires Home Assistant 2026.8.2 or newer.

## Installation

1. In [HACS](https://hacs.xyz/), add this repository as a custom repository (category: Integration) and install **VSS**.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration** and choose **VSS**.

## Configuration

| Field | Description |
| --- | --- |
| Host | Address of your VSS Management Server, including `http://` or `https://`. |
| Port | Defaults to `8081`. |
| Client ID / Client Secret | Generated in the Users section of your VSS dashboard. |

If the server rejects the credentials later on, Home Assistant asks you to reauthenticate. Port and credentials can be changed from the integration's **Reconfigure** action. The update interval (default 5 minutes) is an option on the integration.

## Entities

Each display becomes a device, linked to the VSS server, with:

| Entity | Notes |
| --- | --- |
| Battery, Temperature | |
| Charger | Plugged in or not. |
| Connected | Diagnostic. |
| Firmware | Diagnostic. |
| External battery | Diagnostic; only for displays that report one. |
| Signal strength, Error code, Connect reason | Diagnostic; disabled by default. |

Displays added on the server appear at the next update. Displays removed from the server lose their device automatically, or you can delete them from the device page.

## Diagnostics

Use **Download diagnostics** on the integration page when reporting an issue. The host and credentials are redacted.

## Development

```sh
pip install -r requirements_test.txt
pytest
```

## Additional information

- [vss-python-api](https://pypi.org/project/vss-python-api/)
- [VSS Server Management API](https://api.visionect.com/)
