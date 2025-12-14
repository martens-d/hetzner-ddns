# hetzner-ddns
allows you to use Hetzner Cloud DNS as a DynDNS Provider 

docker run -e ZONE_NAME=example.com \
           -e API_TOKEN=xyz... \
           -e RECORD_TYPE=A \
           -e RECORD_NAME=home \
           -e HETZNER_API_TYPE=cloud \
           martens-d/hetzner-ddns
