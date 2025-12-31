import os
import requests
from typing import List, Dict, Any, Optional

DEBUG = os.getenv("DEBUG", "0").strip().lower() in ("1", "true", "yes", "on")


def _get_token() -> str:
    return os.environ.get('API_TOKEN') or os.environ.get('HETZNER_API_TOKEN') or ''


def _headers(h_type: str, json_content: bool = False) -> Dict[str, str]:
    token = _get_token()
    headers: Dict[str, str] = {}
    if h_type == 'cloud':
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    else:
        headers = {"Auth-API-Token": token, "Accept": "application/json"}
    if json_content:
        headers["Content-Type"] = "application/json"
    return headers


def _normalize_value(rtype: str, value: str) -> str:
    """Normalize record values per type.

    For Hetzner DNS, TXT record values must include quotes in the value
    (e.g., "\"hello\"" when serialized). We wrap with double quotes
    if not already present. Other types are passed through unchanged.
    """
    try:
        rt = (rtype or '').upper()
    except Exception:
        rt = ''
    if rt == 'TXT':
        v = (value or '').strip()
        if not (v.startswith('"') and v.endswith('"')):
            v = f'"{v}"'
        if DEBUG:
            # Avoid printing full sensitive values; show type and length.
            print(f"[DEBUG] normalize TXT value -> len={len(v)}")
        return v
    return value


def list_zones(h_type: str) -> List[Dict[str, Any]]:
    token = _get_token()
    if not token:
        if DEBUG:
            print("[DEBUG] list_zones: no token, fallback to env ZONE_NAME")
        return [{"name": os.environ.get('ZONE_NAME', '')}]

    if h_type == 'dns':
        url = 'https://dns.hetzner.com/api/v1/zones'
        headers = {"Auth-API-Token": token, "Accept": "application/json"}
        if DEBUG:
            print(f"[DEBUG] list_zones: GET {url}")
        r = requests.get(url, headers=headers, timeout=15)
        if DEBUG:
            print(f"[DEBUG] list_zones status={r.status_code}")
        r.raise_for_status()
        data = r.json()
        zones = data.get('zones', [])
        return [{"name": z.get('name', ''), "id": z.get('id', '')} for z in zones]
    else:
        # Optional: Implement cloud zones listing if needed
        if DEBUG:
            print(f"[DEBUG] list_zones: unsupported type '{h_type}', fallback")
        return [{"name": os.environ.get('ZONE_NAME', '')}]


def get_zone_id(h_type: str, zone_name: str) -> str:
    if h_type == 'dns':
        zones = list_zones(h_type)
        for z in zones:
            if z.get('name') == zone_name:
                return z.get('id', '')
        raise RuntimeError(f"Zone '{zone_name}' nicht gefunden")
    else:
        # Attempt cloud zones endpoint; fallback to env if unknown
        token = _get_token()
        if not token:
            raise RuntimeError("Kein API Token gesetzt")
        try:
            url = 'https://api.hetzner.cloud/v1/dns/zones'
            r = requests.get(url, headers=_headers('cloud'), timeout=15)
            r.raise_for_status()
            data = r.json()
            zones = data.get('zones') or data.get('dns_zones') or []
            for z in zones:
                if z.get('name') == zone_name:
                    return z.get('id') or z.get('zone_id') or ''
        except Exception as e:
            if DEBUG:
                print(f"[DEBUG] get_zone_id cloud failed: {e}")
        raise RuntimeError(f"Zone '{zone_name}' nicht gefunden (cloud)")


def get_records(h_type: str, zone_id: str) -> List[Dict[str, Any]]:
    if h_type == 'cloud':
        url = f"https://api.hetzner.cloud/v1/dns/zones/{zone_id}/records"
        r = requests.get(url, headers=_headers('cloud'), timeout=15)
        if DEBUG:
            print(f"[DEBUG] get_records cloud status={r.status_code}")
        r.raise_for_status()
        data = r.json()
        return data.get('records') or data.get('dns_records') or []
    else:
        url = f"https://dns.hetzner.com/api/v1/records?zone_id={zone_id}"
        r = requests.get(url, headers=_headers('dns'), timeout=15)
        if DEBUG:
            print(f"[DEBUG] get_records dns status={r.status_code}")
        r.raise_for_status()
        data = r.json()
        return data.get('records', [])


def create_record(h_type: str, zone_name: str, rtype: str, name: str, value: str, ttl: Optional[int] = None) -> Dict[str, Any]:
    if h_type == 'cloud':
        zid = get_zone_id('cloud', zone_name)
        url = f"https://api.hetzner.cloud/v1/dns/zones/{zid}/records"
        norm_value = _normalize_value(rtype, value)
        payload_rec: Dict[str, Any] = {"type": rtype, "name": name, "value": norm_value}
        if ttl is not None:
            payload_rec["ttl"] = ttl
        payload = {"dns_record": payload_rec}
        r = requests.post(url, headers=_headers('cloud', json_content=True), json=payload, timeout=15)
    else:
        zid = get_zone_id('dns', zone_name)
        url = "https://dns.hetzner.com/api/v1/records"
        norm_value = _normalize_value(rtype, value)
        payload: Dict[str, Any] = {"zone_id": zid, "type": rtype, "name": name, "value": norm_value}
        if ttl is not None:
            payload["ttl"] = ttl
        r = requests.post(url, headers=_headers('dns', json_content=True), json=payload, timeout=15)
    if DEBUG:
        print(f"[DEBUG] create_record POST {url} status={r.status_code}")
    r.raise_for_status()
    return r.json()


def update_record(h_type: str, record_id: str, zone_name: str, rtype: str, name: str, value: str, ttl: Optional[int]) -> Dict[str, Any]:
    if h_type == 'cloud':
        zid = get_zone_id('cloud', zone_name)
        url = f"https://api.hetzner.cloud/v1/dns/zones/{zid}/records/{record_id}"
        norm_value = _normalize_value(rtype, value)
        payload_rec: Dict[str, Any] = {"type": rtype, "name": name, "value": norm_value}
        if ttl is not None:
            payload_rec["ttl"] = ttl
        payload = {"dns_record": payload_rec}
        r = requests.put(url, headers=_headers('cloud', json_content=True), json=payload, timeout=15)
    else:
        url = f"https://dns.hetzner.com/api/v1/records/{record_id}"
        # Hetzner DNS Update requires full record fields.
        zid = get_zone_id('dns', zone_name)
        norm_value = _normalize_value(rtype, value)
        payload: Dict[str, Any] = {
            "zone_id": zid,
            "type": rtype,
            "name": name,
            "value": norm_value,
        }
        if ttl is not None:
            payload["ttl"] = ttl
        r = requests.put(url, headers=_headers('dns', json_content=True), json=payload, timeout=15)
    if DEBUG:
        print(f"[DEBUG] update_record PUT {url} status={r.status_code}")
        try:
            print(f"[DEBUG] update_record response: {r.text}")
        except Exception:
            pass
    r.raise_for_status()
    return r.json()


def delete_record(h_type: str, record_id: str, zone_name: str) -> Dict[str, Any]:
    if h_type == 'cloud':
        zid = get_zone_id('cloud', zone_name)
        url = f"https://api.hetzner.cloud/v1/dns/zones/{zid}/records/{record_id}"
        r = requests.delete(url, headers=_headers('cloud'), timeout=15)
    else:
        url = f"https://dns.hetzner.com/api/v1/records/{record_id}"
        r = requests.delete(url, headers=_headers('dns'), timeout=15)
    if DEBUG:
        print(f"[DEBUG] delete_record DEL {url} status={r.status_code}")
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return {}
