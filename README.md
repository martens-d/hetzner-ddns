# hetzner-ddns
allows you to use Hetzner Cloud DNS as a DynDNS Provider 

docker run -e ZONE_NAME=example.com \
           -e API_TOKEN=tok_abc123 \
           -e RECORD_TYPE=A \
           -e RECORD_NAME=home \
           kutzilla/py-hetzner-ddns
