#!/bin/bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOMAIN="serversilas.ddns.net"
PORT="8000"

echo "Gerando Caddyfile..."
cat <<EOF > "$DIR/Caddyfile"
$DOMAIN {
    tls {
        client_auth {
            mode verify_if_given
            trusted_ca_cert_file /etc/caddy/ca/ca.crt
        }
    }
    reverse_proxy host.docker.internal:$PORT {
        header_up X-Client-Cert-Subject {tls_client_subject}
    }
}
EOF

echo "Limpando containers antigos..."
docker stop caddy-mural >/dev/null 2>&1
docker rm caddy-mural >/dev/null 2>&1

echo "Iniciando Caddy para obter SSL da Let's Encrypt..."
docker run -d \
  --name caddy-mural \
  --restart unless-stopped \
  -p 80:80 \
  -p 443:443 \
  --add-host host.docker.internal:host-gateway \
  -v "$DIR/Caddyfile":/etc/caddy/Caddyfile \
  -v "$DIR/../Server_Web/ca":/etc/caddy/ca \
  -v caddy_data:/data \
  -v caddy_config:/config \
  caddy

echo ""
echo "========================================================"
echo "Servidor rodando!"
echo "O Caddy esta solicitando o certificado [pode levar alguns segundos]"
echo "Acesso: https://$DOMAIN"
echo "========================================================"

read -p "Pressione [Enter] para sair..."  