# Tvheadend Check

Monitor the tuners in your Tvheadend instance.

The check script returns a check for each configured tuner.

## Environment variables

* `TVHEADEND_API_URL`: HTTP URL to your Tvheadend server (default: `http://localhost:9981`)
* `TVHEADEND_API_USERNAME`: Username used to connect to the Tvheadend API
* `TVHEADEND_API_PASSWORD`: Password used to connect to the Tvheadend API
* `TVHEADEND_API_TIMEOUT`: Timeout in seconds for API requests (default: `2`)
* `TVHEADEND_CHECK_NAME`: Check name used for each tuner, `{tuner}` will be replaced with the name of the tuner (default: `Tvheadend_Input_{tuner}`)
* `TVHEADEND_ENABLED_CHECKS`: Comma separated list of enabled checks (default: `ber,unc,transport_errors,continuity_errors,snr`)
* `TVHEADEND_CHECK_CONTINUITY_ERRORS_CRITICAL`: How many continuity errors should be handled as critical (default: `100`)
* `TVHEADEND_CHECK_CONTINUITY_ERRORS_WARNING`: How many continuity errors should be handled as warning (default: `50`)
* `TVHEADEND_CHECK_SNR_SIGNAL_STRENGTH_PERCENTAGE_CRITICAL`: Critical percentage level of the SNR (default: `33`)
* `TVHEADEND_CHECK_SNR_SIGNAL_STRENGTH_PERCENTAGE_WARNING`: Warning percentage level of the SNR (default: `66`)