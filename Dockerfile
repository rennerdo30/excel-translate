FROM python:3.12-slim

WORKDIR /app

COPY certs ./certs
COPY scripts ./scripts
COPY web ./web

ENV HOST=0.0.0.0
ENV PORT=3000

EXPOSE 3000

CMD ["python", "scripts/dev_server.py"]
