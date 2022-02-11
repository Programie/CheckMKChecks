#! /usr/bin/env python3

import os
import re
import requests

from enum import Enum
from requests.auth import HTTPDigestAuth


class State(Enum):
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3


class Checks(Enum):
    BER = "ber"
    UNC = "unc"
    TRANSPORT_ERRORS = "transport_errors"
    CONTINUITY_ERRORS = "continuity_errors"
    SNR = "snr"


def scaled_value(original_value, scale, db_unit):
    max_value = 65535

    if scale == 1:  # Percentage
        calculated_value = original_value / max_value * 100
        return calculated_value, "{}%".format(round(calculated_value))
    elif scale == 2:  # dB
        calculated_value = original_value * 0.001
        return calculated_value, "{} {}".format(round(calculated_value, 1), db_unit)


url = os.getenv("TVHEADEND_API_URL", "http://localhost:9981")
username = os.getenv("TVHEADEND_API_USERNAME")
password = os.getenv("TVHEADEND_API_PASSWORD")
timeout = os.getenv("TVHEADEND_API_TIMEOUT", 2)

check_name = os.getenv("TVHEADEND_CHECK_NAME", "Tvheadend_Input_{tuner}")
enabled_checks = os.getenv("TVHEADEND_ENABLED_CHECKS", ",".join([check.value for check in Checks]))

continuity_errors_critical = int(os.getenv("TVHEADEND_CHECK_CONTINUITY_ERRORS_CRITICAL", 100))
continuity_errors_warning = int(os.getenv("TVHEADEND_CHECK_CONTINUITY_ERRORS_WARNING", 50))

snr_signal_strength_percentage_critical = int(os.getenv("TVHEADEND_CHECK_SNR_SIGNAL_STRENGTH_PERCENTAGE_CRITICAL", 33))
snr_signal_strength_percentage_warning = int(os.getenv("TVHEADEND_CHECK_SNR_SIGNAL_STRENGTH_PERCENTAGE_WARNING", 66))

enabled_checks = list(filter(None, [check.strip() for check in enabled_checks.split(",")]))

inputs_response = requests.get(f"{url}/api/status/inputs", auth=HTTPDigestAuth(username, password), timeout=timeout)

inputs_response.raise_for_status()

inputs = inputs_response.json()["entries"]

for input_object in inputs:
    tuner_name = re.sub(r"\W+", "_", input_object["input"])

    snr = scaled_value(input_object["snr"], input_object["snr_scale"], "dB")
    signal_strength = scaled_value(input_object["signal"], input_object["signal_scale"], "dBm")
    bandwidth = input_object["bps"]
    continuity_errors = input_object["cc"]
    ec_bit = input_object["ec_bit"]
    tc_bit = input_object["tc_bit"]
    unc = input_object["unc"]
    transport_errors = input_object["te"]

    state = State.OK.value
    performance_data = {}
    details = []

    if tc_bit == 0:
        ber = input_object["ber"]
    else:
        ber = ec_bit / tc_bit

    if Checks.BER.value in enabled_checks and ber != 0:
        state = max(state, State.CRITICAL.value)
        details.append("BER = {} (!!)".format(ber))

    performance_data["ber"] = (ber, 1, 1)

    if Checks.UNC.value in enabled_checks and unc != 0:
        state = max(state, State.CRITICAL.value)
        details.append(f"Uncorrected Blocks = {unc} (!!)")

    performance_data["unc"] = (unc, 1, 1)

    if Checks.TRANSPORT_ERRORS.value in enabled_checks and transport_errors != 0:
        state = max(state, State.CRITICAL.value)
        details.append(f"Transport Errors = {transport_errors} (!!)")

    performance_data["transport_errors"] = (transport_errors, 1, 1)

    performance_data["bandwidth"] = bandwidth

    if bandwidth:
        details.append(f"Bandwidth = {bandwidth / 1024} kb/s")

    if Checks.CONTINUITY_ERRORS.value in enabled_checks:
        if continuity_errors > continuity_errors_critical:
            state = max(state, State.CRITICAL.value)
            details.append(f"Continuity Errors = {continuity_errors} (!!)")
        elif continuity_errors > continuity_errors_warning:
            state = max(state, State.WARNING.value)
            details.append(f"Continuity Errors = {continuity_errors} (!)")

    performance_data["continuity_errors"] = (continuity_errors, continuity_errors_warning, continuity_errors_critical)

    if snr is None:
        snr_value = 0
        snr_string = "N/A"
        performance_data["snr"] = 0
    else:
        snr_value, snr_string = snr

        # State calculation currently only possible if SNR is in percent (scale = 1)
        if input_object["snr_scale"] == 1:
            performance_data["snr"] = (snr_value, snr_signal_strength_percentage_warning, snr_signal_strength_percentage_critical)

            if Checks.SNR.value in enabled_checks:
                if snr_value <= snr_signal_strength_percentage_critical:
                    state = max(state, State.CRITICAL.value)
                    snr_string = "{} (!!)".format(snr_string)
                elif snr_value <= snr_signal_strength_percentage_warning:
                    state = max(state, State.WARNING.value)
                    snr_string = "{} (!)".format(snr_string)
        else:
            performance_data["snr"] = snr_value

        details.append("SNR = {}".format(snr_string))

    if signal_strength is None:
        signal_strength_value = 0
        signal_strength_string = "N/A"
        performance_data["signal_strength"] = 0
    else:
        signal_strength_value, signal_strength_string = signal_strength

        # State calculation currently only possible if signal strength is in percent (scale = 1)
        if input_object["signal_scale"] == 1:
            performance_data["signal_strength"] = (signal_strength_value, snr_signal_strength_percentage_warning, snr_signal_strength_percentage_critical)
            if signal_strength_value <= snr_signal_strength_percentage_critical:
                state = max(state, State.CRITICAL.value)
                signal_strength_string = f"{signal_strength_string} (!!)"
            elif signal_strength_value <= snr_signal_strength_percentage_warning:
                state = max(state, State.WARNING.value)
                signal_strength_string = f"{signal_strength_string} (!)"
        else:
            performance_data["signal_strength"] = signal_strength_value

        details.append(f"Signal Strength = {signal_strength_string}")

    if "stream" in input_object:
        active_stream = input_object["stream"]
    else:
        active_stream = "Stream inactive"

    performance_data_string = []

    for key, value in performance_data.items():
        if type(value) == tuple:
            performance_data_string.append("=".join([key, ";".join(map(str, value))]))
        else:
            performance_data_string.append("=".join([key, str(value)]))

    if len(details):
        details_string = "({})".format(", ".join(details))
    else:
        details_string = ""

    check_name = check_name.format(tuner=tuner_name)
    performance_data_string = "|".join(performance_data_string)

    print(f"{state} {check_name} {performance_data_string} {active_stream} {details_string}")
