import os
import sys
import time
import requests

HETZNER_DNS_API_URL = "https://dns.hetzner.com/api/v1"

ZONE_NAME = os.getenv("ZONE_NAME")
API_TOKEN = os.getenv("API_TOKEN")
RECORD_TYPE = os.getenv("RECORD_TYPE", "A")
RECORD_NAME = os.getenv("RECORD_NAME", "@")
USE_UPDATEZONE = os.getenv("HETZNER_DDNS_USE_UPDATEZONE", "false").lower() in ["1", "true", "yes"]

INTERVAL = int(os.getenv("INTERVAL", "300"))  # Interval in seconds

if not (ZONE_NAME and API_TOKEN and RECORD_TYPE and RECORD_NAME):
    print("Please set ZONE_NAME, API_TOKEN, RECORD_TYPE, and RECORD_NAME environment variables.")
    sys.exit(1)

HEADERS = {"Auth-API-Token": API_TOKEN, "Content-Type": "application/json"}

def get_public_ip(record_type):
    if record_type == "AAAA":
        url = "https://api64.ipify.org"
    else:
        url = "https://api.ipify.org"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text.strip()

def get_zone_id():
    resp = requests.get(f"{HETZNER_DNS_API_URL}/zones", headers=HEADERS)
    resp.raise_for_status()
    zones = resp.json().get("zones", [])
    for zone in zones:
        if zone.get("name") == ZONE_NAME:
            return zone.get("id")
    raise Exception(f"Zone {ZONE_NAME} not found.")

def get_record(zone_id):
    resp = requests.get(f"{HETZNER_DNS_API_URL}/records?zone_id={zone_id}", headers=HEADERS)
    resp.raise_for_status()
    records = resp.json().get("records", [])
    for record in records:
        if record.get("type") == RECORD_TYPE and record.get("name") == RECORD_NAME:
            return record
    raise Exception(f"Record {RECORD_TYPE} {RECORD_NAME} not found in zone {ZONE_NAME}.")

def update_record(record_id, zone_id, value, ttl):
    if USE_UPDATEZONE:
        print("Using UpdateZone API (PATCH /zones/{zoneId}) ...")
        # Get all records, replace the value for the target one
        resp = requests.get(f"{HETZNER_DNS_API_URL}/records?zone_id={zone_id}", headers=HEADERS)
        resp.raise_for_status()
        records = resp.json().get("records", [])
        updated_records = []
        for record in records:
            rec = dict(record)
            if rec["id"] == record_id:
                rec["value"] = value
                rec["ttl"] = ttl
            updated_records.append({
                "id": rec["id"],
                "type": rec["type"],
                "name": rec["name"],
                "value": rec["value"],
                "ttl": rec["ttl"]
            })
        patch_data = {"records": updated_records}
        patch_resp = requests.patch(f"{HETZNER_DNS_API_URL}/zones/{zone_id}", headers=HEADERS, json=patch_data)
        patch_resp.raise_for_status()
        result = patch_resp.json()
        # Find and return the updated record
        for rec in result.get("zone", {}).get("records", []):
            if rec["id"] == record_id:
                return rec
        raise Exception(f"Updated record with id {record_id} not found after UpdateZone PATCH.")
    else:
        data = {
            "zone_id": zone_id,
            "type": RECORD_TYPE,
            "name": RECORD_NAME,
            "value": value,
            "ttl": ttl
        }
        resp = requests.put(f"{HETZNER_DNS_API_URL}/records/{record_id}", headers=HEADERS, json=data)
        resp.raise_for_status()
        return resp.json()["record"]

def main_loop():
    last_ip = None
    while True:
        try:
            current_ip = get_public_ip(RECORD_TYPE)
            print(f"Current public IP: {current_ip}")
            zone_id = get_zone_id()
            record = get_record(zone_id)
            print(f"DNS {RECORD_TYPE} record ({RECORD_NAME}) value: {record['value']}")
            if current_ip != record["value"]:
                print(f"IP mismatch, updating record {RECORD_NAME}.{ZONE_NAME} from {record['value']} to {current_ip}")
                updated = update_record(record["id"], zone_id, current_ip, record["ttl"])
                print(f"Record updated: {updated}")
            else:
                print("No update needed.")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main_loop()
