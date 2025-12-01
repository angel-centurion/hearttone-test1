#!/bin/bash
# update-duckdns.sh

DOMAIN="hearttone.duckdns.org"
TOKEN="73ccbc3e-ba79-49f9-97a8-8b872d0ffb08"  # 🔥 REEMPLAZA CON TU TOKEN REAL

# Obtener IP actual de EC2
IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

# Actualizar DuckDNS
curl -s "https://www.duckdns.org/update?domains=$DOMAIN&token=$TOKEN&ip=$IP"

echo "✅ DuckDNS actualizado: $DOMAIN → $IP"
echo "🌐 Tu app estará en: http://$DOMAIN"