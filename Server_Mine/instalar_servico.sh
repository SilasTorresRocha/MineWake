#!/bin/bash

# Script para instalar o monitor do MineWake como serviço Systemd

if [ "$EUID" -ne 0 ]; then
  echo "Por favor, execute este script como root (sudo bash instalar_servico.sh)"
  exit
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SERVICE_FILE="/etc/systemd/system/mine-monitor.service"

echo "Instalando dependencias em um ambiente virtual (venv)..."
apt-get update
apt-get install -y python3-venv python3-pip

# Cria o ambiente virtual
python3 -m venv $DIR/venv

# Instala os pacotes necessários
$DIR/venv/bin/pip install -r $DIR/requirements.txt

echo "Criando o arquivo de serviço Systemd..."
cat > $SERVICE_FILE << EOF
[Unit]
Description=MineWake Monitor
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=$DIR
ExecStart=$DIR/venv/bin/python $DIR/monitor.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

echo "Recarregando daemon do Systemd..."
systemctl daemon-reload

echo "Habilitando serviço para iniciar com o boot..."
systemctl enable mine-monitor.service

echo "Iniciando o serviço agora..."
systemctl start mine-monitor.service

echo "Serviço instalado e rodando! Use 'systemctl status mine-monitor.service' para verificar."
