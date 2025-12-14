# hetzner-ddns

Allows you to use Hetzner Cloud DNS as a DynDNS Provider.

## Features

- Updates A/AAAA records at Hetzner DNS automatically
- **NEU:** Unterstützung für die neue [Hetzner Cloud-DNS API](https://docs.hetzner.cloud/reference/cloud#dns), wählbar per Umgebungsvariable

## Environment Variables

| Variable             | Beschreibung                                              | Pflicht        |
|----------------------|----------------------------------------------------------|---------------|
| `ZONE_NAME`          | Name der DNS Zone (z.B. example.com)                     | ja            |
| `API_TOKEN`          | API Token passend zur API-Art                            | ja            |
| `RECORD_TYPE`        | DNS Record Typ (`A` oder `AAAA`)                         | ja            |
| `RECORD_NAME`        | Name des Records (z.B. `home` oder `@`)                  | ja            |
| `INTERVAL`           | Aktualisierungsintervall in Sekunden (default: 300)      | nein          |
| `HETZNER_API_TYPE`   | `dns` (Standard, alte API) oder `cloud` (neue Cloud-API) | nein (default: `dns`) |

Der richtige `API_TOKEN` muss zu deiner gewählten API passen, siehe [Hetzner DNS Console](https://dns.hetzner.com/) bzw. [Hetzner Cloud Console](https://console.hetzner.cloud/).

## Docker Example

### Standard: Public DNS API
```sh
docker run -e ZONE_NAME=example.com \
           -e API_TOKEN=tok_abc123 \
           -e RECORD_TYPE=A \
           -e RECORD_NAME=home \
           martens-d/hetzner-ddns
```

### NEU: Cloud-API
```sh
docker run -e ZONE_NAME=example.com \
           -e API_TOKEN=hcloud_xxx \
           -e RECORD_TYPE=A \
           -e RECORD_NAME=home \
           -e HETZNER_API_TYPE=cloud \
           martens-d/hetzner-ddns
```

## Hinweise

- Für die Cloud-API brauchst du einen [Hetzner Cloud API-Token](https://console.hetzner.cloud/projects -> Zugriff -> API-Token).
- Die Umgebungsvariable `HETZNER_API_TYPE` steuert, welche API verwendet wird.
