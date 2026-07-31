@echo off
echo Gerando Caddyfile
echo seu-dominio.exemplo.com { > "%~dp0Caddyfile"
echo     tls { >> "%~dp0Caddyfile"
echo         client_auth { >> "%~dp0Caddyfile"
echo             mode verify_if_given >> "%~dp0Caddyfile"
echo             trusted_ca_cert_file /etc/caddy/ca/ca.crt >> "%~dp0Caddyfile"
echo         } >> "%~dp0Caddyfile"
echo     } >> "%~dp0Caddyfile"
echo     reverse_proxy host.docker.internal:8000 { >> "%~dp0Caddyfile"
echo         header_up X-Client-Cert-Subject {tls_client_subject} >> "%~dp0Caddyfile"
echo     } >> "%~dp0Caddyfile"
echo } >> "%~dp0Caddyfile"

echo Iniciando Caddy para obter SSL da Let's Encrypt...
docker stop caddy-mural
docker rm caddy-mural

docker run -d ^
  --name caddy-mural ^
  -p 80:80 ^
  -p 443:443 ^
  --add-host host.docker.internal:host-gateway ^
  -v "%~dp0Caddyfile":/etc/caddy/Caddyfile ^
  -v "%~dp0..\Server_Web\ca":/etc/caddy/ca ^
  -v caddy_data:/data ^
  -v caddy_config:/config ^
  caddy

echo.
echo ========================================================
echo Servidor rodando! 
echo O Caddy esta solicitando o certificado [pode levar alguns segundos]
echo https://seu-dominio.exemplo.com
echo ========================================================
pause