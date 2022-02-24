# VSS for Home Assistant

Integrate this `sensor` by adding this integration as custom repository in [HACS](https://hacs.xyz/). Following, you will be able to add the integration via `Configuration -> Integrations -> VSS API`.

## Config flow

The field `host` is supposed to point at your VSS Management Server address.

The default port is `8081`.

The `client_id` and `client_secret` are generated in the Users section of your VSS dashboard.

## Additional information

- [vss-python-api](https://pypi.org/project/vss-python-api/)
- [VSS Server Management API](https://api.visionect.com/)
