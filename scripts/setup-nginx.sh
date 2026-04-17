#!/usr/bin/env bash
# Artemis — generate self-signed SSL certs and install nginx config.
#
# Usage:
#   ./scripts/setup-nginx.sh              # generate certs + symlink config
#   ./scripts/setup-nginx.sh --regen      # regenerate certs (force overwrite)

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSL_DIR="$PROJECT_ROOT/nginx/ssl"
NGINX_CONF="$PROJECT_ROOT/nginx/artemis.conf"
REGEN=false

for arg in "$@"; do
  case "$arg" in
    --regen) REGEN=true ;;
  esac
done

# ─── Preflight ────────────────────────────────────────────────────

if ! command -v nginx &>/dev/null; then
  echo "ERROR: nginx not found."
  echo "  macOS:  brew install nginx"
  echo "  Linux:  sudo apt install nginx"
  exit 1
fi

if ! command -v openssl &>/dev/null; then
  echo "ERROR: openssl not found."
  exit 1
fi

# ─── Detect nginx config directory ────────────────────────────────

if [ -d "/usr/local/etc/nginx" ]; then
  # macOS Homebrew
  NGINX_DIR="/usr/local/etc/nginx"
  SERVERS_DIR="$NGINX_DIR/servers"
elif [ -d "/opt/homebrew/etc/nginx" ]; then
  # macOS Homebrew (Apple Silicon)
  NGINX_DIR="/opt/homebrew/etc/nginx"
  SERVERS_DIR="$NGINX_DIR/servers"
elif [ -d "/etc/nginx" ]; then
  # Linux
  NGINX_DIR="/etc/nginx"
  SERVERS_DIR="$NGINX_DIR/sites-enabled"
else
  echo "ERROR: Cannot find nginx config directory"
  exit 1
fi

NGINX_SSL_DIR="$NGINX_DIR/ssl"

# ─── Generate self-signed certificate ─────────────────────────────

mkdir -p "$SSL_DIR"

if [ -f "$SSL_DIR/artemis.key" ] && [ "$REGEN" = false ]; then
  echo "SSL certs already exist. Use --regen to regenerate."
else
  echo "Generating self-signed SSL certificate..."

  # Get the machine's local IP for the SAN
  LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null \
    || ifconfig 2>/dev/null | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}' \
    || ip route get 1 2>/dev/null | awk '{print $7; exit}' || echo "")

  # Build SAN entries
  SAN="DNS:localhost,IP:127.0.0.1"
  if [ -n "$LOCAL_IP" ]; then
    SAN="$SAN,IP:$LOCAL_IP"
    echo "  Including local IP in cert: $LOCAL_IP"
  fi

  openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout "$SSL_DIR/artemis.key" \
    -out "$SSL_DIR/artemis.crt" \
    -subj "/CN=artemis-local" \
    -addext "subjectAltName=$SAN" \
    2>/dev/null

  echo "  Certificate generated: $SSL_DIR/artemis.crt"
  echo "  Key generated: $SSL_DIR/artemis.key"
fi

# ─── Install certs to nginx directory ─────────────────────────────

echo "Installing SSL certs to $NGINX_SSL_DIR..."
sudo mkdir -p "$NGINX_SSL_DIR"
sudo cp "$SSL_DIR/artemis.crt" "$NGINX_SSL_DIR/artemis.crt"
sudo cp "$SSL_DIR/artemis.key" "$NGINX_SSL_DIR/artemis.key"
sudo chmod 600 "$NGINX_SSL_DIR/artemis.key"

# ─── Update config paths for this platform ────────────────────────

# Create a platform-specific copy with correct SSL paths
INSTALLED_CONF="$SERVERS_DIR/artemis.conf"
echo "Installing nginx config to $INSTALLED_CONF..."
sudo mkdir -p "$SERVERS_DIR"

# Replace SSL paths in the config to match nginx dir
sed \
  -e "s|/usr/local/etc/nginx/ssl|$NGINX_SSL_DIR|g" \
  "$NGINX_CONF" | sudo tee "$INSTALLED_CONF" > /dev/null

# ─── Test and reload nginx ────────────────────────────────────────

echo "Testing nginx config..."
if sudo nginx -t 2>&1; then
  echo "Reloading nginx..."
  sudo nginx -s reload 2>/dev/null || sudo systemctl reload nginx 2>/dev/null || sudo brew services restart nginx 2>/dev/null || true
  echo ""
  echo "Nginx is configured!"
else
  echo ""
  echo "ERROR: nginx config test failed. Check the output above."
  exit 1
fi

# ─── Summary ──────────────────────────────────────────────────────

echo ""
echo "Artemis is now accessible via HTTPS:"
echo "  Local:   https://localhost"
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null \
    || ifconfig 2>/dev/null | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}' \
    || ip route get 1 2>/dev/null | awk '{print $7; exit}' || echo "")
if [ -n "$LOCAL_IP" ]; then
  echo "  Network: https://$LOCAL_IP"
fi
echo ""
echo "NOTE: Browsers will show a security warning for self-signed certs."
echo "  Chrome: click 'Advanced' -> 'Proceed to site'"
echo "  Safari: click 'Show Details' -> 'visit this website'"
echo "  iOS:    Settings -> General -> About -> Certificate Trust Settings"
echo ""
echo "For remote access, forward port 443 on your router to this machine."
