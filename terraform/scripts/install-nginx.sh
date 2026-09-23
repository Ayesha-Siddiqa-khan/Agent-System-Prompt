#!/bin/bash
set -euo pipefail
echo "[TerraPilot][nginx] Installing Nginx"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y nginx
systemctl enable nginx
cat <<'NGINXCONF' > /etc/nginx/sites-available/default
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    location / {
        proxy_pass http://10.0.1.164:30080;
        proxy_connect_timeout 3s;
        proxy_read_timeout 10s;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINXCONF
systemctl restart nginx
if command -v nginx >/dev/null 2>&1; then
  nginx -v 2>&1
  echo "[TerraPilot][nginx] [OK] nginx installed"
else
  echo "[TerraPilot][nginx] [WARN] nginx command not found after install"
  exit 1
fi
echo "[TerraPilot][nginx] Nginx setup complete"
