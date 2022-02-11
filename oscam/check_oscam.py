#!/usr/bin/python3

import os
import requests
import xmltodict

url = os.getenv("OSCAM_URL", "http://localhost:8888")
timeout = os.getenv("OSCAM_TIMEOUT", 2)
check_name = os.getenv("OSCAM_CHECK_NAME", "OSCam_Cards")

url = f"{url}/oscamapi.html?part=status"

per_card_state = {}

xml = xmltodict.parse(requests.get(url, timeout=timeout).content)

for client in xml["oscam"]["status"]["client"]:
    if client["@type"] == "p" or client["@type"] == "r":
        per_card_state[client["@name"]] = client["connection"]["#text"]

cards_total = len(per_card_state)
cards_good = sum(1 for state in per_card_state.values() if state == "CARDOK" or state == "CONNECTED")
cards_bad = cards_total - cards_good

if cards_bad:
    state = 2  # Critical
else:
    state = 0  # OK

print(f"{state} {check_name} count={cards_total}|good={cards_good}|bad={cards_bad} {cards_total} cards, {cards_bad} bad, {cards_good} good")
