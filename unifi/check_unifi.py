#! /usr/bin/env python3

import os
import re
import sys

from enum import Enum

from pyunifi.controller import Controller

host = os.getenv("UNIFI_API_HOST", "localhost")
port = int(os.getenv("UNIFI_API_PORT", "8443"))
username = os.getenv("UNIFI_API_USERNAME")
password = os.getenv("UNIFI_API_PASSWORD")
site_id = os.getenv("UNIFI_API_SITEID", "default")
expected_uplink_speed = os.getenv("UNIFI_UPLINK_SPEED")
cert_path = os.getenv("UNIFI_CERT_PATH", "")

if cert_path.lower().strip() in ["yes", "true"]:
    cert_path = True
elif cert_path.lower().strip() in ["no", "false"]:
    cert_path = False
elif not cert_path:
    cert_dir = os.getenv("CERTDIR")
    cert_name = os.getenv("CERTNAME")

    if cert_dir and cert_name:
        cert_path = os.path.join(cert_dir, cert_name)
    else:
        cert_path = True


class State(Enum):
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Y", suffix)


controller = Controller(host=host, port=port, username=username, password=password, site_id=site_id, ssl_verify=cert_path)

ap_clients = {}

for client in controller.get_clients():
    ap_mac = client["ap_mac"]

    if ap_mac not in ap_clients:
        ap_clients[ap_mac] = []

    ap_clients[ap_mac].append(client)

for ap in controller.get_aps():
    try:
        ap_mac = ap["mac"]

        if ap_mac in ap_clients:
            clients = ap_clients[ap_mac]
        else:
            clients = []

        status = State.OK.value
        status_text = []

        if ap["state"] == 1:
            status = max(status, State.OK.value)
            status_text.append("Online")
        else:
            status = max(status, State.CRITICAL.value)
            status_text.append("Offline (!!)")

        uplink_speed = int(ap.get("uplink", {}).get("speed", 0))

        if expected_uplink_speed is not None:
            expected_uplink_speed = int(expected_uplink_speed)

            if uplink_speed != expected_uplink_speed:
                status = max(status, State.CRITICAL.value)
                status_text.append(f"Uplink: {uplink_speed} MBit/s but expected {expected_uplink_speed} MBit/s (!!)")

        client_count = len(clients)

        performance_data = {
            "rx_bytes": ap["rx_bytes"],
            "tx_bytes": ap["tx_bytes"],
            "uptime": ap["uptime"],
            "uplink_speed": uplink_speed,
            "clients": client_count
        }

        performance_data_array = []

        for key, value in performance_data.items():
            performance_data_array.append("=".join([key, value]))

        escaped_ap_name = re.sub(r"\W+", "_", ap["name"])
        performance_data_string = "|".join(performance_data_array)
        rx_bytes_string = sizeof_fmt(ap["rx_bytes"])
        tx_bytes_string = sizeof_fmt(ap["tx_bytes"])

        status_text.append(f"{client_count} clients")
        status_text.append(f"Traffic: {rx_bytes_string} up / {tx_bytes_string} down")

        status_text = ", ".join(status_text)

        print(f"{status} UniFi_Controller_{escaped_ap_name} {performance_data_string} {status_text}")
    except BaseException as exception:
        print(exception, file=sys.stderr)
