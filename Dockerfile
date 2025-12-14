FROM python:3.11-alpine

WORKDIR /app
COPY hetzner_ddns.py .

RUN pip install requests

ENV HETZNER_API_TYPE=dns

ENTRYPOINT ["python", "hetzner_ddns.py"]
