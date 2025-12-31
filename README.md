# hetzner-ddns

Allows you to use Hetzner DNS as a DynDNS Provider.

**English below** / **English instructions see below**

---

## Deutsch

### Funktionen

- Aktualisiert A/AAAA-Records automatisch bei Hetzner DNS
- **Neu:** Unterstützung für die neue [Hetzner Cloud DNS-API](https://docs.hetzner.cloud/reference/cloud#dns), über eine Environment-Variable wählbar

### Umgebungsvariablen

| Variable             | Beschreibung                                             | Pflicht | Default            |
|----------------------|----------------------------------------------------------|---------|--------------------|
| `ZONE_NAME`          | Name der DNS Zone (z.B. example.com)                     | ja      | –                  |
| `API_TOKEN`          | API Token passend zur API-Art                            | ja      | –                  |
| `RECORD_TYPE`        | DNS Record Typ (`A` oder `AAAA`)                         | ja      | `A`                |
| `RECORD_NAME`        | Name des Records (z.B. `home` oder `@`)                  | ja      | `@`                |
| `INTERVAL`           | Aktualisierungsintervall in Sekunden                     | nein    | 300                |
| `HETZNER_API_TYPE`   | `dns` (Standard, alte API) oder `cloud` (neue Cloud-API) | nein    | `dns`              |
| `DEBUG`              | Gibt API-Responses im Terminal aus (1/true/yes/on)       | nein    | `0`                |
| `SHOW_TABLE`         | Zeigt alle Records als Tabelle im Browser (1/true/yes/on)| nein    | `0`                |

Achte darauf, dass der API Token zur gewählten API passt, siehe [Hetzner DNS Console](https://dns.hetzner.com/) bzw. [Hetzner Cloud Console](https://console.hetzner.cloud/).

### Beispiel: Docker Run

#### Standard: Public DNS API
```sh
docker run -e ZONE_NAME=example.com \
           -e API_TOKEN=tok_abc123 \
           -e RECORD_TYPE=A \
           -e RECORD_NAME=home \
           martens-d/hetzner-ddns
```

#### NEU: Cloud-API
```sh
docker run -e ZONE_NAME=example.com \
           -e API_TOKEN=hcloud_xxx \
           -e RECORD_TYPE=A \
           -e RECORD_NAME=home \
           -e HETZNER_API_TYPE=cloud \
           martens-d/hetzner-ddns
```

### Beispiel: Docker Compose

```yaml
services:
  hetzner-ddns:
    image: martens-d/hetzner-ddns
    environment:
      - ZONE_NAME=example.com
      - API_TOKEN=tok_abc123
      - RECORD_TYPE=A
      - RECORD_NAME=home
      # - HETZNER_API_TYPE=cloud  # für die neue Cloud-API einfügen
```

### Hinweise

- Für die Cloud-API brauchst du einen [Hetzner Cloud API-Token](https://console.hetzner.cloud/projects -> Zugriff -> API-Token).
- Die Umgebungsvariable `HETZNER_API_TYPE` steuert, welche API verwendet wird.
- **DEBUG:** Setze die Umgebungsvariable `DEBUG=1` (oder `true`/`yes`/`on`), um die vollständigen API-Responses im Terminal auszugeben (z.B. für Debugging oder Support).

---

## English

### Features

- Automatically updates A/AAAA records with Hetzner DNS
- **New:** Support for new [Hetzner Cloud DNS API](https://docs.hetzner.cloud/reference/cloud#dns) selectable via environment variable

### Environment Variables

| Variable             | Description                                              | Required | Default    |
|----------------------|----------------------------------------------------------|----------|------------|
| `ZONE_NAME`          | The DNS zone name (e.g. example.com)                     | yes      | –          |
| `API_TOKEN`          | API token for your selected API                          | yes      | –          |
| `RECORD_TYPE`        | DNS record type (`A` or `AAAA`)                          | yes      | `A`        |
| `RECORD_NAME`        | Record name (e.g. `home` or `@`)                         | yes      | `@`        |
| `INTERVAL`           | Update interval in seconds                               | no       | 300        |
| `HETZNER_API_TYPE`   | `dns` (default: legacy API) or `cloud` (new Cloud API)   | no       | `dns`      |
| `DEBUG`              | Print API responses to terminal (1/true/yes/on)          | no       | `0`        |
| `SHOW_TABLE`         | Show all records as table in browser (1/true/yes/on)     | no       | `0`        |

Please make sure your API token matches the selected API: see [Hetzner DNS Console](https://dns.hetzner.com/) or [Hetzner Cloud Console](https://console.hetzner.cloud/).

### Example: Docker Run

#### Default: Public DNS API
```sh
docker run -e ZONE_NAME=example.com \
           -e API_TOKEN=tok_abc123 \
           -e RECORD_TYPE=A \
           -e RECORD_NAME=home \
           martens-d/hetzner-ddns
```

#### NEW: Cloud API
```sh
docker run -e ZONE_NAME=example.com \
           -e API_TOKEN=hcloud_xxx \
           -e RECORD_TYPE=A \
           -e RECORD_NAME=home \
           -e HETZNER_API_TYPE=cloud \
           martens-d/hetzner-ddns
```

### Example: Docker Compose

```yaml
services:
  hetzner-ddns:
    image: martens-d/hetzner-ddns
    environment:
      - ZONE_NAME=example.com
      - API_TOKEN=tok_abc123
      - RECORD_TYPE=A
      - RECORD_NAME=home
      # - HETZNER_API_TYPE=cloud  # enable for new cloud API
```

### Notes

- For the Cloud API, create a [Hetzner Cloud API token](https://console.hetzner.cloud/projects -> Access -> API tokens).
- The environment variable `HETZNER_API_TYPE` switches between APIs (`dns` for legacy, `cloud` for new Cloud API).
- **DEBUG:** Set the environment variable `DEBUG=1` (or `true`/`yes`/`on`) to print full API responses to the terminal (useful for debugging or support).
