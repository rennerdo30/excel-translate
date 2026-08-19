FROM python:3.12-slim

WORKDIR /app

# certs/ is deliberately NOT copied: baking a TLS private key into an image
# layer would ship it with every tag and push. Mount it at runtime instead
# (docker-compose.yml mounts ./certs read-only).
COPY scripts ./scripts
COPY web ./web

ENV HOST=0.0.0.0
ENV PORT=3000

EXPOSE 3000

CMD ["python", "scripts/dev_server.py"]
