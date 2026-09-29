# Changelog

## 0.7

### Breaking

- Requires Home Assistant 2026.8.2 or newer.

### Fixed

- Link displays to the hub with `via_device_id`. The old `via_device` parameter is
  deprecated and stops working in Home Assistant 2027.8.0.
- Displays added on the VSS server now appear without reloading the integration, and
  displays that were removed lose their device.
- A display reporting an empty `Displays` list no longer breaks the battery sensor.
- The config flow tells rejected credentials (`invalid_auth`) apart from connection
  problems (`cannot_connect`) and checks for a duplicate server before connecting.

### Added

- Reauthentication and reconfigure flows.
- Options flow to change the update interval (default 5 minutes).
- Diagnostic entities: connected, signal strength (disabled by default), firmware, error
  code (disabled by default), connect reason (disabled by default) and, when the display
  reports one, external battery.
- Diagnostics download with the host and credentials redacted.
- Displays can be deleted from the device page once the server no longer reports them.
- The device model comes from the API when it provides one.
- Tests and GitHub Actions for tests, hassfest and HACS validation.

### Changed

- Store setup objects in `entry.runtime_data`, use entity descriptions and translated
  entity names. Entity IDs and unique IDs of existing entities are unchanged.
- The battery sensor keeps its attributes for compatibility with existing templates.
