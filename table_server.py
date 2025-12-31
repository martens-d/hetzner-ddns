from http.server import BaseHTTPRequestHandler, HTTPServer
from string import Template
import os
import json
from urllib.parse import urlparse, parse_qs
import requests
import hetzner_api

def _labels() -> dict:
  """Load labels from i18n.json based on LANG, flatten to dot-keys.

  Fallbacks: if file or language missing, use minimal English defaults.
  """
  lang = (os.environ.get('LANG') or '').strip().lower() or 'en'
  i18n_path = os.path.join(os.path.dirname(__file__), "i18n.json")

  def _flatten(obj, prefix="", out=None):
    if out is None:
      out = {}
    if isinstance(obj, dict):
      for k, v in obj.items():
        key = f"{prefix}.{k}" if prefix else k
        _flatten(v, key, out)
    else:
      out[prefix] = obj
    return out

  try:
    with open(i18n_path, "r", encoding="utf-8") as f:
      all_i18n = json.load(f)
    # Build case-insensitive map of available languages
    lower_map = {k.lower(): k for k in all_i18n.keys()}
    base = lang.split('-')[0]
    chosen_key = None
    # Exact match first (e.g., de-de → de-DE)
    if lang in lower_map:
      chosen_key = lower_map[lang]
    # Then exact base language match (e.g., de)
    if not chosen_key and base in lower_map:
      chosen_key = lower_map[base]
    # Then any available regional variant starting with base- (e.g., de-AT, pt-BR)
    if not chosen_key:
      for k in sorted(all_i18n.keys()):
        kl = k.lower()
        if kl.startswith(base + '-'):
          chosen_key = k
          break
    # English fallback (en or en-*)
    if not chosen_key:
      en_key = None
      for k in all_i18n.keys():
        kl = k.lower()
        if kl == 'en' or kl.startswith('en-'):
          en_key = k
          break
      chosen_key = en_key or next(iter(all_i18n.keys()), None)

    lang_dict = all_i18n.get(chosen_key, {})
    flat = _flatten(lang_dict)
    # Provide critical fallbacks if keys are missing
    flat.setdefault('title', 'DNS Records')
    flat.setdefault('sidebar.title', 'Zones')
    flat.setdefault('columns.name', 'Name')
    flat.setdefault('columns.type', 'Type')
    flat.setdefault('columns.value', 'Value')
    flat.setdefault('columns.ttl', 'TTL')
    flat.setdefault('columns.actions', 'Actions')
    flat.setdefault('buttons.edit', 'Edit')
    flat.setdefault('buttons.delete', 'Delete')
    flat.setdefault('buttons.add', 'Add Record')
    flat.setdefault('modal.title.confirm', 'Confirm Action')
    flat.setdefault('modal.title.edit', 'Edit Record')
    flat.setdefault('modal.title.add', 'Add Record')
    flat.setdefault('modal.title.delete', 'Confirm Delete')
    flat.setdefault('modal.labels.zone', 'Zone')
    flat.setdefault('modal.labels.type', 'Type')
    flat.setdefault('modal.labels.name', 'Name')
    flat.setdefault('modal.labels.value', 'Value')
    flat.setdefault('modal.labels.ttl', 'TTL')
    flat.setdefault('modal.ttl.none', 'None')
    flat.setdefault('modal.actions.cancel', 'Cancel')
    flat.setdefault('modal.actions.ok', 'OK')
    return flat
  except Exception:
    # Hard fallback if i18n.json is missing or invalid
    return {
      'title': 'DNS Records',
      'sidebar.title': 'Zones',
      'columns.name': 'Name',
      'columns.type': 'Type',
      'columns.value': 'Value',
      'columns.ttl': 'TTL',
      'columns.actions': 'Actions',
      'buttons.edit': 'Edit',
      'buttons.delete': 'Delete',
      'buttons.add': 'Add Record',
      'modal.title.confirm': 'Confirm Action',
      'modal.title.edit': 'Edit Record',
      'modal.title.add': 'Add Record',
      'modal.title.delete': 'Confirm Delete',
      'modal.labels.zone': 'Zone',
      'modal.labels.type': 'Type',
      'modal.labels.name': 'Name',
      'modal.labels.value': 'Value',
      'modal.labels.ttl': 'TTL',
      'modal.ttl.none': 'None',
      'modal.actions.cancel': 'Cancel',
      'modal.actions.ok': 'OK',
    }
DEBUG = os.getenv("DEBUG", "0").strip().lower() in ("1", "true", "yes", "on")


def generate_table_html(records):
  labels = _labels()
  def row_html(r):
    rid = r.get('id', '')
    name = r.get('name')
    rtype = r.get('type')
    value = r.get('value')
    ttl = r.get('ttl')
    # Actions cell with edit/delete buttons, carrying data-* for JS
    actions = (
      f"<td class='actions-cell' data-id='{rid}' data-name='{name}' data-type='{rtype}' data-value='{value}' data-ttl='{ttl}'>"
      f"<button class='icon-btn btn-edit' title='{labels['buttons.edit']}' data-i18n-title='buttons.edit' aria-label='{labels['buttons.edit']}'>"
      f"<svg viewBox='0 0 24 24' class='icon'><path d='M3 21h6l12-12-6-6L3 15v6zM14 4l6 6'/></svg></button>"
      f"<button class='icon-btn btn-delete' title='{labels['buttons.delete']}' data-i18n-title='buttons.delete' aria-label='{labels['buttons.delete']}'>"
      f"<svg viewBox='0 0 24 24' class='icon'><path d='M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14'/></svg></button>"
      f"</td>"
    )
    return (
      f"<tr data-record-id='{rid}'>"
      f"<td class='name-cell'>{name}</td><td class='type-cell'>{rtype}</td><td class='value-col'>{value}</td><td class='ttl-cell'>{ttl}</td>" + actions + "</tr>"
    )

  rows = "\n".join(row_html(r) for r in records)
  # Footer row with add button
  footer = (
    "<tr class='add-row'>"
    "<td colspan='5' class='add-row-cell'>"
    f"<button class='icon-btn btn-add' title='{labels['buttons.add']}' data-i18n-title='buttons.add' aria-label='{labels['buttons.add']}'>"
    "<svg viewBox='0 0 24 24' class='icon'><path d='M12 5v14M5 12h14'/></svg>"
    "</button>"
    "</td>"
    "</tr>"
  )
  return (
    "<table class='ddns-table'>"
    f"<thead><tr>"
    f"<th class='name-col' data-i18n='columns.name'>{labels['columns.name']}</th>"
    f"<th class='type-col' data-i18n='columns.type'>{labels['columns.type']}</th>"
    f"<th data-i18n='columns.value'>{labels['columns.value']}</th>"
    f"<th class='ttl-col' data-i18n='columns.ttl'>{labels['columns.ttl']}</th>"
    f"<th class='actions-col' data-i18n='columns.actions'>{labels['columns.actions']}</th>"
    f"</tr></thead>"
    "<tbody>" + rows + footer + "</tbody>"
    "</table>"
  )


def run_table_server(get_zone_id_dns, get_zone_id_cloud, get_record_dns, get_record_cloud, ZONE_NAME, HETZNER_API_TYPE):

    class TableHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if DEBUG:
                print(f"[DEBUG] HTTP GET {self.path}")
            # Static CSS delivery
            if self.path == "/style.css":
                try:
                    css_path = os.path.join(os.path.dirname(__file__), "style.css")
                    with open(css_path, "r", encoding="utf-8") as f:
                        css = f.read()
                    self.send_response(200)
                    self.send_header("Content-type", "text/css; charset=utf-8")
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    self.wfile.write(css.encode("utf-8"))
                except Exception as e:
                    self.send_response(404)
                    self.send_header("Content-type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(f"CSS not found: {e}".encode("utf-8"))
                return

            # i18n JSON delivery
            if self.path == "/i18n.json":
              try:
                i18n_path = os.path.join(os.path.dirname(__file__), "i18n.json")
                with open(i18n_path, "r", encoding="utf-8") as f:
                  content = f.read()
                self.send_response(200)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
              except Exception as e:
                self.send_response(404)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"i18n not found: {e}"}).encode("utf-8"))
              return

            # Zones API
            if self.path.startswith('/api/zones'):
                try:
                    zones = self.list_zones()
                    self.send_response(200)
                    self.send_header("Content-type", "application/json; charset=utf-8")
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    self.wfile.write(json.dumps({"zones": zones}).encode("utf-8"))
                    if DEBUG:
                        print(f"[DEBUG] /api/zones returned {len(zones)} zones")
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-type", "application/json; charset=utf-8")
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                    if DEBUG:
                        print(f"[DEBUG] /api/zones error: {e}")
                return

            # Records API
            if self.path.startswith('/api/records'):
                try:
                    q = parse_qs(urlparse(self.path).query)
                    zone_name = q.get('zone_name', [os.environ.get('ZONE_NAME', '')])[0]
                    if DEBUG:
                      print(f"[DEBUG] /api/records for zone '{zone_name}'")
                    records = self.fetch_records_for_zone(zone_name)
                    if DEBUG:
                      print(f"[DEBUG] /api/records list ({len(records)}):")
                      for r in records:
                        try:
                          print(f"  - name={r.get('name')} type={r.get('type')} value={r.get('value')} ttl={r.get('ttl')}")
                        except Exception as _e:
                          print(f"  - record raw: {r}")
                    html = generate_table_html(records)
                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    self.wfile.write(html.encode("utf-8"))
                    if DEBUG:
                      print(f"[DEBUG] /api/records returned {len(records)} records; html.len={len(html)}")
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-type", "text/plain; charset=utf-8")
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Expires", "0")
                    self.end_headers()
                    self.wfile.write(f"Error: {e}".encode("utf-8"))
                    if DEBUG:
                      print(f"[DEBUG] /api/records error: {e}")
                return

            # Dynamic HTML delivery (page)
            try:
              initial_zone_name = os.environ.get('ZONE_NAME', '')
              if HETZNER_API_TYPE == "cloud":
                zone_id = hetzner_api.get_zone_id('cloud', initial_zone_name)
                records = hetzner_api.get_records('cloud', zone_id)
              else:
                zone_id = hetzner_api.get_zone_id('dns', initial_zone_name)
                records = hetzner_api.get_records('dns', zone_id)
              if DEBUG:
                print(f"[DEBUG] Page init: type={HETZNER_API_TYPE}, zone='{initial_zone_name}', zone_id={zone_id}, records={len(records)}")
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"<h1>Error</h1><pre>{e}</pre>".encode("utf-8"))
                return

            table_html = generate_table_html(records)
            # determine refresh interval in ms from env INTERVAL (seconds)
            try:
                _refresh_sec = int(os.environ.get('INTERVAL', '60'))
            except ValueError:
                _refresh_sec = 60
            if _refresh_sec < 5:
                _refresh_sec = 5
            if _refresh_sec > 3600:
                _refresh_sec = 3600
            _refresh_ms = _refresh_sec * 1000
            # Load external HTML template file
            tmpl_path = os.path.join(os.path.dirname(__file__), "index.html")
            try:
                with open(tmpl_path, "r", encoding="utf-8") as f:
                    tmpl_str = f.read()
            except Exception as e:
                # Fallback minimal page if template file missing
                if DEBUG:
                    print(f"[DEBUG] Failed to load template {tmpl_path}: {e}")
                tmpl_str = "<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>Hetzner DNS Records</title></head><body><h1>DNS Records</h1><div id=\"zone-info\"></div><div id=\"table-slot\">${table_html}</div></body></html>"
            tmpl = Template(tmpl_str)
            _lang_override = (os.environ.get('LANG') or '').strip()
            # Use base-language of override for html lang, default to 'en'
            _html_lang = ( _lang_override.split('-')[0].lower() if _lang_override else 'en' ) or 'en'
            html = tmpl.substitute(
                json_zone_name=json.dumps(ZONE_NAME),
                refresh_ms=_refresh_ms,
                debug_js=('true' if DEBUG else 'false'),
                table_html=table_html,
              lang_override_json=json.dumps(_lang_override),
              html_lang=_html_lang,
              i18n_title=_labels().get('title','DNS Records'),
              i18n_sidebar_title=_labels().get('sidebar.title','Zones'),
              i18n_modal_confirm=_labels().get('modal.title.confirm','Confirm Action'),
              i18n_modal_edit=_labels().get('modal.title.edit','Edit Record'),
              i18n_modal_add=_labels().get('modal.title.add','Add Record'),
              i18n_modal_delete=_labels().get('modal.title.delete','Confirm Delete'),
              i18n_label_zone=_labels().get('modal.labels.zone','Zone'),
              i18n_label_type=_labels().get('modal.labels.type','Type'),
              i18n_label_name=_labels().get('modal.labels.name','Name'),
              i18n_label_value=_labels().get('modal.labels.value','Value'),
              i18n_label_ttl=_labels().get('modal.labels.ttl','TTL'),
              i18n_ttl_none=_labels().get('modal.ttl.none','None'),
              i18n_modal_cancel=_labels().get('modal.actions.cancel','Cancel'),
              i18n_modal_ok=_labels().get('modal.actions.ok','OK')
            )
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        def do_POST(self):
            # Simple JSON body reader
            try:
              length = int(self.headers.get('Content-Length', '0'))
            except Exception:
              length = 0
            body = self.rfile.read(length) if length > 0 else b''
            try:
              data = json.loads(body.decode('utf-8')) if body else {}
            except Exception:
              data = {}
            if DEBUG:
              print(f"[DEBUG] HTTP POST {self.path} body={data}")

            # API headers are handled in hetzner_api

            # Create record
            if self.path.startswith('/api/record/create'):
              try:
                zone_name = data.get('zone_name') or os.environ.get('ZONE_NAME', '')
                rtype = data.get('type')
                name = data.get('name')
                value = data.get('value')
                ttl = data.get('ttl') or 300
                resp = hetzner_api.create_record(HETZNER_API_TYPE, zone_name, rtype, name, value, ttl)
                self.send_response(200)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode('utf-8'))
              except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
              return

            # Update record
            if self.path.startswith('/api/record/update'):
              try:
                rid = data.get('id')
                zone_name = data.get('zone_name') or os.environ.get('ZONE_NAME', '')
                rtype = data.get('type')
                name = data.get('name')
                value = data.get('value')
                ttl = data.get('ttl')
                resp = hetzner_api.update_record(HETZNER_API_TYPE, rid, zone_name, rtype, name, value, ttl)
                self.send_response(200)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode('utf-8'))
              except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
              return

            # Delete record
            if self.path.startswith('/api/record/delete'):
              try:
                rid = data.get('id')
                zone_name = data.get('zone_name') or os.environ.get('ZONE_NAME', '')
                resp = hetzner_api.delete_record(HETZNER_API_TYPE, rid, zone_name)
                self.send_response(200)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode('utf-8'))
              except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
              return

            # Unknown
            self.send_response(404)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not Found"}).encode('utf-8'))

        def list_zones(self):
          return hetzner_api.list_zones(HETZNER_API_TYPE)

        def fetch_records_for_zone(self, zone_name: str):
          if DEBUG:
            print(f"[DEBUG] fetch_records_for_zone: zone_name='{zone_name}' type={HETZNER_API_TYPE}")
          if HETZNER_API_TYPE == 'cloud':
            zid = hetzner_api.get_zone_id('cloud', zone_name)
            recs = hetzner_api.get_records('cloud', zid)
            if DEBUG:
              print(f"[DEBUG] fetch_records_for_zone: zone_id={zid}, records={len(recs)}")
            return recs
          else:
            zid = hetzner_api.get_zone_id('dns', zone_name)
            recs = hetzner_api.get_records('dns', zid)
            if DEBUG:
              print(f"[DEBUG] fetch_records_for_zone: zone_id={zid}, records={len(recs)}")
            return recs

    server_address = ("", 8080)
    httpd = HTTPServer(server_address, TableHandler)
    print(f"Table-Server läuft auf http://localhost:{server_address[1]}")
    httpd.serve_forever()
