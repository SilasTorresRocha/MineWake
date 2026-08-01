#!/bin/bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOMAIN_VPN="sua-api.exemplo.com"
PORT_VPN="8000"

DOMAIN_PC="seu-dominio.exemplo.com"
PORT_PC="8080"

echo "Gerando Caddyfile Unificado..."
cat <<EOF > "$DIR/Caddyfile"
{
    key_type rsa2048
}

$DOMAIN_VPN {
    reverse_proxy host.docker.internal:$PORT_VPN
}

$DOMAIN_PC {
    tls {
        client_auth {
            mode verify_if_given
            trusted_ca_cert_file /etc/caddy/ca/ca.crt
        }
    }
    reverse_proxy host.docker.internal:$PORT_PC {
        header_up -X-Client-Cert-Subject
        header_up X-Client-Cert-Subject {tls_client_subject}
    }
}
EOF

echo "Limpando containers antigos..."
docker stop caddy-VPN >/dev/null 2>&1
docker rm caddy-VPN >/dev/null 2>&1
docker stop caddy-mural >/dev/null 2>&1
docker rm caddy-mural >/dev/null 2>&1

echo "Iniciando Caddy unificado para obter SSL da Let's Encrypt (VPN + PC)..."
docker run -d \
  --name caddy-VPN \
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
echo "Servidor rodando na base do RSA 2048!"
echo "Dominios ativos:"
echo " - $DOMAIN_VPN (Apontando para VPN na porta $PORT_VPN)"
echo " - $DOMAIN_PC (Apontando para MineWake na porta $PORT_PC com mTLS)"
echo "========================================================"
read -p "Pressione [Enter] para sair..."
