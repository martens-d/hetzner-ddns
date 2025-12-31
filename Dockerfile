FROM python:3.11-alpine

WORKDIR /app
# Copy application modules and assets needed by the table server
COPY hetzner_ddns.py ./
COPY hetzner_api.py ./
COPY table_server.py ./
COPY index.html ./
COPY i18n.json ./
COPY style.css ./
COPY docker-entrypoint.sh ./

RUN pip install --no-cache-dir requests \
 && chmod +x docker-entrypoint.sh

# Optional: document the port used by the table server
EXPOSE 8080

ENTRYPOINT ["./docker-entrypoint.sh"]
