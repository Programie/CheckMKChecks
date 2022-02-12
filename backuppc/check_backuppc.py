#! /usr/bin/env python3

import os
import requests
import sys

from collections import OrderedDict


class CheckMK:
    STATUS_OK = 0
    STATUS_WARNING = 1
    STATUS_CRITICAL = 2
    STATUS_UNKNOWN = 3

    @staticmethod
    def build_performance_data_string(data=None):
        if data is None or not data:
            return "-"

        entries = []

        for name, values in data.items():
            string_values = []

            if not isinstance(values, (list, tuple)):
                values = [values]

            for value in values:
                if value is None:
                    value = ""
                else:
                    value = str(value)

                string_values.append(value)

            entries.append("=".join([name, ";".join(string_values)]))

        return "|".join(entries)

    @staticmethod
    def print(status, check_name, perfdata, message):
        perfdata_string = CheckMK.build_performance_data_string(perfdata)

        sys.stdout.buffer.write(f"{status} {check_name} {perfdata_string} {message}\n".encode("utf-8"))


def main():
    url = os.getenv("BACKUPPC_URL", "http://localhost")
    username = os.getenv("BACKUPPC_USERNAME")
    password = os.getenv("BACKUPPC_PASSWORD")
    timeout = os.getenv("BACKUPPC_TIMEOUT", 2)

    states_strings = {
        "Status_idle": "idle",
        "Status_backup_starting": "backup starting",
        "Status_backup_in_progress": "backup in progress",
        "Status_restore_starting": "restore starting",
        "Status_restore_in_progress": "restore in progress",
        "Status_admin_pending": "link pending",
        "Status_admin_running": "link running"
    }

    reason_strings = {
        "Reason_backup_done": "done",
        "Reason_restore_done": "restore done",
        "Reason_archive_done": "archive done",
        "Reason_nothing_to_do": "idle",
        "Reason_backup_failed": "backup failed",
        "Reason_restore_failed": "restore failed",
        "Reason_archive_failed": "archive failed",
        "Reason_no_ping": "no ping",
        "Reason_backup_canceled_by_user": "backup canceled by user",
        "Reason_restore_canceled_by_user": "restore canceled by user",
        "Reason_archive_canceled_by_user": "archive canceled by user",
        "Disabled_OnlyManualBackups": "auto disabled",
        "Disabled_AllBackupsDisabled": "disabled"
    }

    response = requests.get(f"{url}/BackupPC_Admin", params={"action": "metrics", "format": "json"}, auth=(username, password), timeout=timeout)
    response.raise_for_status()
    response_json = response.json()

    check_state = CheckMK.STATUS_OK
    running_backups = 0
    failed_backups = 0
    messages = []

    hosts = OrderedDict(sorted(response_json["hosts"].items()))

    for hostname, host_data in hosts.items():
        state = host_data["state"]
        reason = host_data["reason"]
        message = host_data["error"] or states_strings.get(state, "")

        if state in ["Status_backup_starting", "Status_backup_in_progress"]:
            running_backups += 1

        if reason == "Reason_backup_failed":
            failed_backups += 1

        if reason in ["Reason_backup_done", "Reason_restore_done", "Reason_archive_done", "Reason_nothing_to_do", "Reason_no_ping"]:
            host_state = CheckMK.STATUS_OK
        else:
            host_state = CheckMK.STATUS_WARNING
            reason_string = reason_strings.get(reason, "")
            message = f"(!){reason_string}: {message}"

        check_state = max(check_state, host_state)
        messages.append(f"{hostname}: {message}")

    perfdata = {
        "pool_size": response_json.get("cpool", {}).get("size", 0),
        "running": [running_backups, 0, 0, 0, len(hosts)],
        "failed": [failed_backups, 0, 0, 0, len(hosts)],
        "hosts": len(hosts)
    }

    messages.insert(0, f"{len(hosts)} hosts, {running_backups} running, {failed_backups} failed")

    CheckMK.print(check_state, "BackupPC", perfdata, "\\n".join(messages))


if __name__ == "__main__":
    main()
