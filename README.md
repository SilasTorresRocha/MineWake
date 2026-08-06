# MineWake

**MineWake** é um sistema de gerenciamento remoto para servidores de Minecraft, focado em economia de energia e facilidade de uso. Ele foi projetado para rodar em duas máquinas separadas, permitindo que os jogadores liguem o servidor sob demanda através de uma interface web.

## Arquitetura do Projeto

O projeto é dividido em dois componentes principais:

### 1. `Server_Web` (Interface de Controle)
Uma aplicação web construída com **FastAPI** que atua como o painel de controle para os jogadores. 
- **Funcionalidades:** Mostra o status do servidor, tempo restante antes de desligar, e permite ligar o servidor físico remotamente via **Wake-on-LAN (WoL)**.
- **Segurança:** Utiliza autenticação baseada em certificados de cliente (mTLS / Client Certificates) gerenciada pelo Caddy, garantindo que apenas usuários com certificados válidos acessem o painel.
- **Administração:** Possui um painel interno de administração, onde é possível gerar e revogar tokens/certificados (salvos em um banco SQLite `certificados.db`).

### 2. `Server_Mine` (Servidor de Minecraft)
A máquina principal ou serviço onde roda o servidor de jogo (Vanilla ou ModPack) em um contêiner **Docker**.
- **Monitoramento Automático:** Roda um script de serviço (`monitor.py`) em background que pinga o servidor, lê o status via RCON/Ping e se comunica com o `Server_Web` através de Webhooks.
- **Auto-Shutdown:** Monitora a presença de jogadores. Se o servidor ficar vazio pelo tempo limite (`timeout_minutos`), ele processa o desligamento do servidor, economizando energia e processamento.

## Como Funciona na Prática

1. O site do **MineWake (`Server_Web`)** fica sempre online (hospedado em um Orange Pi).
2. O jogador autorizado acessa a interface web. Se a máquina do **Minecraft (`Server_Mine`)** estiver desligada, ele aperta o botão "Ligar Servidor" no site.
3. O `Server_Web` envia um **Magic Packet (WoL)** na rede local para ligar o hardware do servidor de Minecraft.
4. Assim que a máquina liga, o Docker inicia o container do Minecraft e o script envia um webhook atualizando o status no site para "Online".
5. Quando o último jogador sai, um timer regressivo se inicia. Se ninguém entrar até o timer zerar, o sistema desliga o servidor novamente.

## Tecnologias Utilizadas

- **Backend / Scripts:** Python, FastAPI, Jinja2, Uvicorn
- **Infraestrutura:** Docker e Docker Compose
- **Rede / Comunicação:** Wake-on-LAN (WoL), Webhooks, RCON
- **Segurança / Web:** Caddy (Reverse Proxy + mTLS), SQLite
- **Sistema Operacional:** Linux (scripts em bash para configuração de serviços e WoL via `ethtool`)

## Estrutura e Configuração Básica

As definições globais que interligam os dois serviços estão no arquivo `config_geral.yml`:
- `minecraft_mac`: MAC address essencial para enviar o pacote de Wake-on-LAN.
- `ip_orange_pi` / `ip_server_mine`: Endereços IPs das maquinas.
- `timeout_minutos`: O tempo sem jogadores antes do servidor desligar.
- Credenciais e porta do protocolo `RCON`.

> **Nota sobre o Wake-on-Lan (WoL):** 
> Para que o `Server_Mine` possa ser ligado, a placa mãe e a interface de rede da máquina devem estar configuradas para aceitar "Magic Packets". Nas distribuições Linux (Debian/Ubuntu), geralmente utiliza-se o pacote `ethtool` para habilitar a escuta (`wol g`), e é recomendado fixar isso criando um serviço no `systemd` para não perder a configuração ao reiniciar.

---
*Projeto em desenvolvimento. No futuro, há planos para facilitar a implantação unificando serviços, caso necessário.*