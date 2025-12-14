FROM python:3.11-alpine

WORKDIR /app
COPY hetzner_ddns.py .
COPY docker-entrypoint.sh .
RUN pip install requests
RUN chmod +x docker-entrypoint.sh

ENTRYPOINT ["./docker-entrypoint.sh"]
