#!/bin/bash
# deploy-aws.sh

echo "🚀 INICIANDO DESPLIEGUE EN AWS..."

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker si no existe
if ! command -v docker &> /dev/null; then
    echo "Instalando Docker..."
    sudo apt install -y docker.io docker-compose
    sudo usermod -aG docker $USER
    newgrp docker
fi

# Crear directorios necesarios
mkdir -p instance
sudo chown -R $USER:$USER instance

# Configurar DuckDNS
echo "🔧 Configurando DuckDNS..."
DOMAIN="hearttone.duckdns.org"
TOKEN="73ccbc3e-ba79-49f9-97a8-8b872d0ffb08"  # 🔥 REEMPLAZA CON TU TOKEN REAL

IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
curl -s "https://www.duckdns.org/update?domains=$DOMAIN&token=$TOKEN&ip=$IP"

echo "✅ DuckDNS actualizado: $DOMAIN → $IP"

# Configurar cron para DuckDNS
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/ubuntu/update-duckdns.sh >> /home/ubuntu/duckdns.log 2>&1") | crontab -

# Construir y levantar contenedores
echo "🐳 Construyendo contenedores..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Esperar y verificar
echo "⏳ Esperando que los servicios inicien..."
sleep 30

echo "📊 ESTADO FINAL:"
docker-compose ps

echo "🌐 VERIFICANDO CONEXIÓN:"
curl -s http://localhost/health && echo "✅ Nginx funcionando"

echo ""
echo "🎉 ¡DESPLIEGUE COMPLETADO!"
echo "========================================"
echo "🌐 URL PRINCIPAL: http://$DOMAIN"
echo "🔧 PANEL ADMIN:   http://$DOMAIN/admin"
echo "========================================"