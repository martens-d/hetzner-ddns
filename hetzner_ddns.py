import os
import sys
import time
import requests

print("starting up!")

# API URLs
HETZNER_DNS_API_URL = "https://dns.hetzner.com/api/v1"
HETZNER_CLOUD_API_URL = "https://api.hetzner.cloud/v1"

# Environment Variables
ZONE_NAME = os.getenv("ZONE_NAME")
API_TOKEN = os.getenv("API_TOKEN")
RECORD_TYPE = os.getenv("RECORD_TYPE", "A")
RECORD_NAME = os.getenv("RECORD_NAME", "@")
INTERVAL = int(os.getenv("INTERVAL", "300"))  # Interval in seconds
# NEW: Choose API type: "dns" (default) or "cloud"
HETZNER_API_TYPE = os.getenv("HETZNER_API_TYPE", "dns").lower()
# DEBUG-Variable
DEBUG = os.getenv("DEBUG", "0").strip().lower() in ("1", "true", "yes", "on")

# Validate required ENV
if not (ZONE_NAME and API_TOKEN and RECORD_TYPE and RECORD_NAME):
  print("Please set ZONE_NAME, API_TOKEN, RECORD_TYPE, and RECORD_NAME environment variables.")
  sys.exit(1)

def get_headers():
  if HETZNER_API_TYPE == "cloud":
    return {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
  else:
    return {"Auth-API-Token": API_TOKEN, "Content-Type": "application/json"}

def get_public_ip(record_type):
  if record_type == "AAAA":
    url = "https://api64.ipify.org"
  else:
    url = "https://api.ipify.org"
  resp = requests.get(url)
  resp.raise_for_status()
  return resp.text.strip()

def get_zone_id_dns():
  resp = requests.get(f"{HETZNER_DNS_API_URL}/zones", headers=get_headers())
  if DEBUG:
    print("[DEBUG] Response von /zones:", resp.text)
  resp.raise_for_status()
  zones = resp.json().get("zones", [])
  for zone in zones:
    if zone.get("name") == ZONE_NAME:
      return zone.get("id")
  raise Exception(f"Zone {ZONE_NAME} not found (DNS API).")

def get_zone_id_cloud():
  # List all zones in the Hetzner Cloud DNS API
  # ref: https://docs.hetzner.cloud/reference/cloud#get-api-v1-dns-zones
  resp = requests.get(f"{HETZNER_CLOUD_API_URL}/dns/zones", headers=get_headers())
  if DEBUG:
    print("[DEBUG] Response von /dns/zones:", resp.text)
  resp.raise_for_status()
  zones = resp.json().get("dns_zones", [])
  for zone in zones:
    if zone.get("name") == ZONE_NAME:
      return zone.get("id")
  raise Exception(f"Zone {ZONE_NAME} not found (Cloud API).")

def get_record_dns(zone_id):
  resp = requests.get(f"{HETZNER_DNS_API_URL}/records?zone_id={zone_id}", headers=get_headers())
  if DEBUG:
    print(f"[DEBUG] Response von /records?zone_id={zone_id}:", resp.text)
  resp.raise_for_status()
  records = resp.json().get("records", [])
  for record in records:
    if record.get("type") == RECORD_TYPE and record.get("name") == RECORD_NAME:
      return record
  raise Exception(f"Record {RECORD_TYPE} {RECORD_NAME} not found in zone {ZONE_NAME} (DNS API).")

def get_record_cloud(zone_id):
  # ref: https://docs.hetzner.cloud/reference/cloud#get-api-v1-dns-zones-zone_id-records
  resp = requests.get(f"{HETZNER_CLOUD_API_URL}/dns/zones/{zone_id}/records", headers=get_headers())
  if DEBUG:
    print(f"[DEBUG] Response von /dns/zones/{zone_id}/records:", resp.text)
  resp.raise_for_status()
  records = resp.json().get("dns_records", [])
  for record in records:
    if record.get("type") == RECORD_TYPE and record.get("name") == RECORD_NAME:
      return record
  raise Exception(f"Record {RECORD_TYPE} {RECORD_NAME} not found in zone {ZONE_NAME} (Cloud API).")

def update_record_dns(record_id, zone_id, value, ttl):
  data = {
    "zone_id": zone_id,
    "type": RECORD_TYPE,
    "name": RECORD_NAME,
    "value": value,
    "ttl": ttl
  }
  resp = requests.put(f"{HETZNER_DNS_API_URL}/records/{record_id}", headers=get_headers(), json=data)
  if DEBUG:
    print(f"[DEBUG] Response von PUT /records/{record_id}:", resp.text)
  resp.raise_for_status()
  return resp.json()["record"]

def update_record_cloud(record_id, zone_id, value, ttl):
  data = {
    "type": RECORD_TYPE,
    "name": RECORD_NAME,
    "value": value,
    "ttl": ttl
  }
  resp = requests.put(
    f"{HETZNER_CLOUD_API_URL}/dns/zones/{zone_id}/records/{record_id}",
    headers=get_headers(),
    json={"dns_record": data}
  )
  if DEBUG:
    print(f"[DEBUG] Response von PUT /dns/zones/{zone_id}/records/{record_id}:", resp.text)
  resp.raise_for_status()
  return resp.json()["dns_record"]

def main_loop():
  last_ip = None
  while True:
    try:
     current_ip = get_public_ip(RECORD_TYPE)
     print(f"Current public IP: {current_ip}")

     if HETZNER_API_TYPE == "cloud":
       zone_id = get_zone_id_cloud()
       record = get_record_cloud(zone_id)
       print(f"(Cloud API) DNS {RECORD_TYPE} record ({RECORD_NAME}) value: {record['value']}")
       if current_ip != record["value"]:
         print(f"IP mismatch, updating record {RECORD_NAME}.{ZONE_NAME} from {record['value']} to {current_ip}")
         updated = update_record_cloud(record["id"], zone_id, current_ip, record["ttl"])
         print(f"Record updated: {updated}")
       else:
         print(f"No DNS update required for {RECORD_NAME}.{ZONE_NAME} with IP {current_ip}")
     else:
       zone_id = get_zone_id_dns()
       record = get_record_dns(zone_id)
       print(f"(DNS API) DNS {RECORD_TYPE} record ({RECORD_NAME}) value: {record['value']}")
       if current_ip != record["value"]:
         print(f"IP mismatch, updating record {RECORD_NAME}.{ZONE_NAME} from {record['value']} to {current_ip}")
         updated = update_record_dns(record["id"], zone_id, current_ip, record["ttl"])
         print(f"Record updated: {updated}")
       else:
         print(f"No DNS update required for {RECORD_NAME}.{ZONE_NAME} with IP {current_ip}")
    except Exception as e:
      print(f"Error: {e}")
    time.sleep(INTERVAL)

if __name__ == "__main__":
  main_loop()