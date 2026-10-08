# Always-on host for the Ferrara commercial demo.
# The app listens on 0.0.0.0. Cloudflare Tunnel is optional via TUNNEL_TOKEN.
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
  && rm -rf /var/lib/apt/lists/* \
  && curl -fsSL -o /usr/local/bin/cloudflared \
    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
  && chmod +x /usr/local/bin/cloudflared

COPY app ./app
COPY scripts/start_hosted.sh ./scripts/start_hosted.sh
COPY sql ./sql
RUN chmod +x ./scripts/start_hosted.sh \
  && mkdir -p /app/data

ENV HOST=0.0.0.0
ENV PORT=8772
ENV PYTHONUNBUFFERED=1

EXPOSE 8772
CMD ["./scripts/start_hosted.sh"]
