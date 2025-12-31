
import os
import sys
import time
import requests

if os.getenv("SHOW_TABLE", "0").strip().lower() in ("1", "true", "yes", "on"):
  from table_server import run_table_server

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
# SHOW_TABLE Variable
SHOW_TABLE = os.getenv("SHOW_TABLE", "0").strip().lower() in ("1", "true", "yes", "on")
# START_BACKGROUND_UPDATE steuert das Starten des DDNS-Updaters
START_BACKGROUND_UPDATE = os.getenv("START_BACKGROUND_UPDATE", "1").strip().lower() in ("1", "true", "yes", "on")

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
  # Read target zone from current environment to support dynamic selection
  zone_target = os.getenv("ZONE_NAME")
  resp = requests.get(f"{HETZNER_DNS_API_URL}/zones", headers=get_headers())
  if DEBUG:
    print("[DEBUG] Response von /zones:", resp.text)
  resp.raise_for_status()
  zones = resp.json().get("zones", [])
  for zone in zones:
    if zone.get("name") == zone_target:
      return zone.get("id")
  raise Exception(f"Zone {zone_target} not found (DNS API).")

def get_zone_id_cloud():
  # Read target zone from current environment to support dynamic selection
  # ref: https://docs.hetzner.cloud/reference/cloud#get-api-v1-dns-zones
  zone_target = os.getenv("ZONE_NAME")
  resp = requests.get(f"{HETZNER_CLOUD_API_URL}/dns/zones", headers=get_headers())
  if DEBUG:
    print("[DEBUG] Response von /dns/zones:", resp.text)
  resp.raise_for_status()
  zones = resp.json().get("dns_zones", [])
  for zone in zones:
    if zone.get("name") == zone_target:
      return zone.get("id")
  raise Exception(f"Zone {zone_target} not found (Cloud API).")

def get_record_dns(zone_id):
  resp = requests.get(f"{HETZNER_DNS_API_URL}/records?zone_id={zone_id}", headers=get_headers())
  if DEBUG:
    print(f"[DEBUG] Response von /records?zone_id={zone_id}:", resp.text)
  resp.raise_for_status()
  records = resp.json().get("records", [])
  return records

def get_record_cloud(zone_id):
  # ref: https://docs.hetzner.cloud/reference/cloud#get-api-v1-dns-zones-zone_id-records
  resp = requests.get(f"{HETZNER_CLOUD_API_URL}/dns/zones/{zone_id}/records", headers=get_headers())
  if DEBUG:
    print(f"[DEBUG] Response von /dns/zones/{zone_id}/records:", resp.text)
  resp.raise_for_status()
  records = resp.json().get("dns_records", [])
  return records

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
        records = get_record_cloud(zone_id)
        # Suche nach passendem Record
        record = next((r for r in records if r.get("type") == RECORD_TYPE and r.get("name") == RECORD_NAME), None)
        if record:
          print(f"(Cloud API) DNS {RECORD_TYPE} record ({RECORD_NAME}) value: {record['value']}")
          if current_ip != record["value"]:
            print(f"IP mismatch, updating record {RECORD_NAME}.{ZONE_NAME} from {record['value']} to {current_ip}")
            updated = update_record_cloud(record["id"], zone_id, current_ip, record["ttl"])
            print(f"Record updated: {updated}")
          else:
            print(f"No DNS update required for {RECORD_NAME}.{ZONE_NAME} with IP {current_ip}")
        else:
          print(f"Record {RECORD_TYPE} {RECORD_NAME} not found in zone {ZONE_NAME} (Cloud API).")
      else:
        zone_id = get_zone_id_dns()
        records = get_record_dns(zone_id)
        record = next((r for r in records if r.get("type") == RECORD_TYPE and r.get("name") == RECORD_NAME), None)
        if record:
          print(f"(DNS API) DNS {RECORD_TYPE} record ({RECORD_NAME}) value: {record['value']}")
          if current_ip != record["value"]:
            print(f"IP mismatch, updating record {RECORD_NAME}.{ZONE_NAME} from {record['value']} to {current_ip}")
            updated = update_record_dns(record["id"], zone_id, current_ip, record["ttl"])
            print(f"Record updated: {updated}")
          else:
            print(f"No DNS update required for {RECORD_NAME}.{ZONE_NAME} with IP {current_ip}")
        else:
          print(f"Record {RECORD_TYPE} {RECORD_NAME} not found in zone {ZONE_NAME} (DNS API).")
    except Exception as e:
      print(f"Error: {e}")
    time.sleep(INTERVAL)


if __name__ == "__main__":
  import threading
  # Fälle:
  # 1) Beide aktiv: Updater im Hintergrund + Table-Server im Vordergrund
  # 2) Nur Updater: main_loop() blockierend
  # 3) Nur Table: nur run_table_server()
  # 4) Nichts: sauber beenden
  if SHOW_TABLE and START_BACKGROUND_UPDATE:
    t = threading.Thread(target=main_loop, daemon=True)
    t.start()
    run_table_server(
      get_zone_id_dns=get_zone_id_dns,
      get_zone_id_cloud=get_zone_id_cloud,
      get_record_dns=get_record_dns,
      get_record_cloud=get_record_cloud,
      ZONE_NAME=ZONE_NAME,
      HETZNER_API_TYPE=HETZNER_API_TYPE
    )
  elif START_BACKGROUND_UPDATE and not SHOW_TABLE:
    main_loop()
  elif SHOW_TABLE and not START_BACKGROUND_UPDATE:
    run_table_server(
      get_zone_id_dns=get_zone_id_dns,
      get_zone_id_cloud=get_zone_id_cloud,
      get_record_dns=get_record_dns,
      get_record_cloud=get_record_cloud,
      ZONE_NAME=ZONE_NAME,
      HETZNER_API_TYPE=HETZNER_API_TYPE
    )
  else:
    print("Weder START_BACKGROUND_UPDATE noch SHOW_TABLE aktiv – nichts zu tun. Beende.")
    sys.exit(0)