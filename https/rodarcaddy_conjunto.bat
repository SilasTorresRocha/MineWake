@echo off
set "DIR=%~dp0"
set "DOMAIN_VPN=apisilas.ddns.net"
set "PORT_VPN=8000"

set "DOMAIN_PC=serversilas.ddns.net"
set "PORT_PC=8080"

echo Gerando Caddyfile Unificado...
echo { > "%~dp0Caddyfile"
echo     key_type rsa2048 >> "%~dp0Caddyfile"
echo } >> "%~dp0Caddyfile"
echo. >> "%~dp0Caddyfile"

echo %DOMAIN_VPN% { >> "%~dp0Caddyfile"
echo     reverse_proxy host.docker.internal:%PORT_VPN% >> "%~dp0Caddyfile"
echo } >> "%~dp0Caddyfile"
echo. >> "%~dp0Caddyfile"

echo %DOMAIN_PC% { >> "%~dp0Caddyfile"
echo     tls { >> "%~dp0Caddyfile"
echo         client_auth { >> "%~dp0Caddyfile"
echo             mode verify_if_given >> "%~dp0Caddyfile"
echo             trusted_ca_cert_file /etc/caddy/ca/ca.crt >> "%~dp0Caddyfile"
echo         } >> "%~dp0Caddyfile"
echo     } >> "%~dp0Caddyfile"
echo     reverse_proxy host.docker.internal:%PORT_PC% { >> "%~dp0Caddyfile"
echo         header_up X-Client-Cert-Subject {tls_client_subject} >> "%~dp0Caddyfile"
echo     } >> "%~dp0Caddyfile"
echo } >> "%~dp0Caddyfile"

echo Limpando containers antigos...
docker stop caddy-VPN >nul 2>&1
docker rm caddy-VPN >nul 2>&1
docker stop caddy-mural >nul 2>&1
docker rm caddy-mural >nul 2>&1

echo Iniciando Caddy unificado para obter SSL da Let's Encrypt (VPN + PC)...
docker run -d ^
  --name caddy-VPN ^
  --restart unless-stopped ^
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
echo Servidor rodando na base do RSA 2048!
echo Dominios ativos:
echo  - %DOMAIN_VPN% (Apontando para VPN na porta %PORT_VPN%)
echo  - %DOMAIN_PC% (Apontando para MineWake na porta %PORT_PC% com mTLS)
echo ========================================================
pause
