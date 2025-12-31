# hetzner-ddns

Allows you to use Hetzner DNS as a DynDNS Provider.

**English below** / **English instructions see below**

---

## Deutsch

> [!WARNING]
> HETZNER_API_TYPE=cloud nicht getestet

### Funktionen

- Aktualisiert A/AAAA-Records automatisch bei Hetzner DNS
- **Neu:** Unterstützung für die neue [Hetzner Cloud DNS-API](https://docs.hetzner.cloud/reference/cloud#dns), über eine Environment-Variable wählbar
- **Neu:** Interaktive Tabelle (Web-UI) mit Aktionen pro Record (Bearbeiten/Löschen/Hinzufügen).

### Umgebungsvariablen

| Variable                  | Beschreibung                                                 | Pflicht | Default            |
|---------------------------|--------------------------------------------------------------|---------|--------------------|
| `ZONE_NAME`               | Name der DNS Zone (z.B. example.com)                         | ja      | –                  |
| `API_TOKEN`               | API Token passend zur API-Art                                | ja      | –                  |
| `RECORD_TYPE`             | DNS Record Typ (`A` oder `AAAA`)                             | ja      | `A`                |
| `RECORD_NAME`             | Name des Records (z.B. `home` oder `@`)                      | ja      | `@`                |
| `INTERVAL`                | Aktualisierungsintervall in Sekunden                         | nein    | 300                |
| `HETZNER_API_TYPE`        | `dns` (Standard, alte API) oder `cloud` (neue Cloud-API)     | nein    | `dns`              |
| `DEBUG`                   | Gibt API-Responses im Terminal aus (1/true/yes/on)           | nein    | `0`                |
| `SHOW_TABLE`              | Zeigte Web-UI für alle Records des API_TOKEN (1/true/yes/on) | nein    | `0`                |
| `START_BACKGROUND_UPDATE` | Deaktiviert die automatisch Aktualisierung (0/false/no/off)  | nein    | `1`                |
| `LANG`                    | stetzt die Sprache für die Web-UI (de/en/fr/pt-BR)           | nein    | `en` (fallback)    |

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
    ports:
      - 80:8080
    environment:
      - ZONE_NAME=example.com
      - API_TOKEN=tok_abc123
      - RECORD_TYPE=A
      - RECORD_NAME=home
      # - HETZNER_API_TYPE=cloud     # für die neue Cloud-API einfügen
      # - SHOW_TABLE=1               # für die neue Web-UI
      # - START_BACKGROUND_UPDATE=0  # schaltet den automatischen Hintergrundservice ab
      # - LANG=de                    # Sprache für die Web-UI (aktuell: de, en (Fallback), fr oder pt-BR)
```

### Hinweise

- Für die Cloud-API brauchst du einen [Hetzner Cloud API-Token](https://console.hetzner.cloud/projects -> Zugriff -> API-Token).
- Die Umgebungsvariable `HETZNER_API_TYPE` steuert, welche API verwendet wird.
- **DEBUG:** Setze die Umgebungsvariable `DEBUG=1` (oder `true`/`yes`/`on`), um die vollständigen API-Responses im Terminal auszugeben (z.B. für Debugging oder Support).

---

## English

> [!WARNING]
> HETZNER_API_TYPE=cloud not tested

### Features

- Automatically updates A/AAAA records with Hetzner DNS
- **New:** Support for new [Hetzner Cloud DNS API](https://docs.hetzner.cloud/reference/cloud#dns) selectable via environment variable
- **New:** Interactive table (Web-UI) with per-record edit/delete/add actions.

### Environment Variables

| Variable                  | Description                                              | Required | Default         |
|---------------------------|----------------------------------------------------------|----------|-----------------|
| `ZONE_NAME`               | The DNS zone name (e.g. example.com)                     | yes      | –               |
| `API_TOKEN`               | API token for your selected API                          | yes      | –               |
| `RECORD_TYPE`             | DNS record type (`A` or `AAAA`)                          | yes      | `A`             |
| `RECORD_NAME`             | Record name (e.g. `home` or `@`)                         | yes      | `@`             |
| `INTERVAL`                | Update interval in seconds                               | no       | 300             |
| `HETZNER_API_TYPE`        | `dns` (default: legacy API) or `cloud` (new Cloud API)   | no       | `dns`           |
| `DEBUG`                   | Print API responses to terminal (1/true/yes/on)          | no       | `0`             |
| `SHOW_TABLE`              | Show Web-UI for all records of API_TOKEN (1/true/yes/on) | no       | `0`             |
| `START_BACKGROUND_UPDATE` | disables automatic records updates (0/false/no/off)      | no       | `1`             |
| `LANG`                    | set language for Web-UI (de/en/fr/pt-BR)                 | no       | `en` (fallback) |

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
    ports:
      - 80:8080
    environment:
      - ZONE_NAME=example.com
      - API_TOKEN=tok_abc123
      - RECORD_TYPE=A
      - RECORD_NAME=home
      # - HETZNER_API_TYPE=cloud     # enable for new cloud API
      # - SHOW_TABLE=1               # enable for new Web-UI
      # - START_BACKGROUND_UPDATE=0  # disables automatic background updates (if you just want the Web-UI)
      # - LANG=de                    # language for Web-UI (current: de, en (fallback), fr or pt-BR)
```

### Notes

- For the Cloud API, create a [Hetzner Cloud API token](https://console.hetzner.cloud/projects -> Access -> API tokens).
- The environment variable `HETZNER_API_TYPE` switches between APIs (`dns` for legacy, `cloud` for new Cloud API).
- **DEBUG:** Set the environment variable `DEBUG=1` (or `true`/`yes`/`on`) to print full API responses to the terminal (useful for debugging or support).
