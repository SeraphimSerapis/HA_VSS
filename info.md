# VSS for Home Assistant

Integrate this `sensor` with the following snippet:

```yaml
platform: vss
host: !secret vss_host
client_id: !secret vss_client_id
client_secret: !secret vss_client_secret
```

The field `host` is supposed to point at port `8081` of your VSS setup. The `client_id` and `client_secret` are generated in the Users section of your VSS dashboard.

Add `vss` into your Home Assistant's `custom_components` folder.

Additional reference:

- [vss-python-api](https://pypi.org/project/vss-python-api/)
- [VSS Server Management API](https://api.visionect.com/)
