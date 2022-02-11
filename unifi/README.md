# UniFi Check

Monitor UniFi access points (online state and uplink speed).

The check script returns a check for each access point.

## Environment variables

* `UNIFI_API_HOST`: UniFI Controller host (default: `localhost`)
* `UNIFI_API_PORT`: UniFI Controller port (default: `8443`)
* `UNIFI_API_USERNAME` Username used to connect to the UniFi Controller (required)
* `UNIFI_API_PASSWORD`: Password used to connect to the UniFi Controller (required)
* `UNIFI_API_SITEID`: ID of the site which should be used (default: `default`)
* `UNIFI_UPLINK_SPEED`: Expected uplink speed of the access points, keep empty or undefined to disable (default: None)
* `UNIFI_CERT_PATH`: Path to the certificate used for TLS verification, can also be `true` or `yes` to use the default CA bundle, `false` or `no` to disable verification (default: `true`)

If `UNIFI_CERT_PATH` is not set but `CERTDIR` and `CERTNAME` are set, those variables will be used as path for `UNIFI_CERT_PATH` (to be compatible with the [jacobalberty/unifi](https://hub.docker.com/r/jacobalberty/unifi) Docker image).