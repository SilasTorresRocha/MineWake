# MineWake
MineWake
Esse Projeto consiste em rodar em 2 maquinas separadas(mas estou vendo a possosibilidade de poder rodar em uma maquina so com docker (versao futuras talvez)). Server_Mine é onde vai rodar o servidor de Minecraft e ele e quem vai chamar o arquivo do servidor seja de ModPack ou Vanilla. o Server_Web e onde vai rodar o site do MineWake, ele vai hospedar uma paquina web os usuario vai poder acessar e poder ligar acionar o server mine, prorogar/renovar tempo de desligamento automatico do server1.

(Depois termino isso)


Linus server_mine wake_on_lan:



Instale o pacote de gerenciamento de rede:
sudo apt update
sudo apt install ethtool

Descubra o nome da interface de rede:

ip a


(Geralmente começa com enp ou eth, como enp3s0 ou eth0)



Ative a escuta do pacote mágico:

sudo ethtool -s NOME_DA_INTERFACE wol g


(Para confirmar se o sistema operacional aceitou a configuração, você pode rodar o comando sudo ethtool NOME_DA_INTERFACE (sem o -s). Se a resposta contiver a linha Wake-on: g, a sua máquina já está pronta para ser acordada remotamente pela placa de rede.)


[por algum motivo o wake on lan volta ao padrao entao acho que isso deve resolver:
"
sudo tee /etc/systemd/system/wol.service << EOF
[Unit]
Description=Configurar Wake-on-LAN

[Service]
Type=oneshot
ExecStart=/usr/sbin/ethtool -s enp6s0 wol g

[Install]
WantedBy=basic.target
EOF

sudo systemctl enable wol
sudo systemctl start wol

"

]