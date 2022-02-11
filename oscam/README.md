# OSCam Cards Check

Checks the state (good/bad) of the cards in your OSCam instance.

The check script returns a single check for all configured cards.

## Environment variables

* `OSCAM_URL`: URL to your OSCam instance (default: `http://localhost:8888`)
* `OSCAM_TIMEOUT`: Timeout in seconds for API requests (default: `2`)
* `OSCAM_CHECK_NAME`: Check name to use (default: `OSCam_Cards`)