# BackupPC Check

Check the state of all configured backup clients in your [BackupPC](https://backuppc.github.io/backuppc) instance.

The script returns a single check for all clients.

## Environment variables

* `BACKUPPC_URL`: URL to your BackupPC instance (default: `http://localhost`)
* `BACKUPPC_USERNAME`: Username used to connect to the BackupPC API
* `BACKUPPC_PASSWORD`: Password used to connect to the BackupPC API
* `BACKUPPC_TIMEOUT`: Timeout in seconds for API requests (default: `2`)