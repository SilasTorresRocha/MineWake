import time
import subprocess
import os
import re
import yaml
import requests
from mcrcon import MCRcon

# Caminho para o config_geral.yml
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, 'config_geral.yml')

def carregar_config():
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)

def jogadores_online(host, port, password):
    try:
        with MCRcon(host, password, port=port) as mcr:
            response = mcr.command("/list")
            #"There are 0 of a max of 20 players online: "
            # Extrai o primeiro numero que aparece
            match = re.search(r'there are (\d+)', response.lower())
            if match:
                return int(match.group(1))
            return 0
    except Exception as e:
        print(f"Erro ao conectar no RCON: {e}")
        return -1 # Indica erro na conexao 

def notificar_web(ip_orange_pi, porta, jogadores, status, tempo_restante=None):
    url = f"http://{ip_orange_pi}:{porta}/api/webhook"
    dados = {
        "status": status,
        "jogadores": jogadores,
        "tempo_restante_minutos": tempo_restante
    }
    try:
        requests.post(url, json=dados, timeout=5)
    except Exception as e:
        print(f"Erro ao notificar Server_Web: {e}")

def atualizar_server_properties(config):
    properties_file = os.path.join(BASE_DIR, 'Server_Mine', 'minecraft_data', 'server.properties')
    if not os.path.exists(properties_file):
        print("server.properties não encontrado. Será criado pelo Minecraft depois.")
        return

    rcon_port = str(config['rcon']['porta'])
    rcon_pass = str(config['rcon']['senha'])
    
    with open(properties_file, 'r') as f:
        linhas = f.readlines()
        
    configuracoes = {
        'enable-rcon': 'true',
        'rcon.port': rcon_port,
        'rcon.password': rcon_pass,
        'broadcast-rcon-to-ops': 'false'
    }
    
    modificado = False
    for i, linha in enumerate(linhas):
        for chave in list(configuracoes.keys()):
            if linha.startswith(chave + '='):
                nova_linha = f"{chave}={configuracoes[chave]}\n"
                if linha != nova_linha:
                    linhas[i] = nova_linha
                    modificado = True
                del configuracoes[chave]
                break
                
    for chave, valor in configuracoes.items():
        linhas.append(f"{chave}={valor}\n")
        modificado = True
        
    if modificado:
        with open(properties_file, 'w') as f:
            f.writelines(linhas)
        print("server.properties atualizado com o RCON do config_geral.yml!")

def main():
    print("Iniciando Monitor do MineWake...")
    
    config = carregar_config()
    container_name = config.get('minecraft_nome_container', 'mine-server')
    
    print("Injetando configurações de RCON no servidor...")
    atualizar_server_properties(config)
    
    # Garante que o container do Minecraft inicie junto com o monitor
    print(f"Garantindo que o container '{container_name}' inicie...")
    subprocess.run(["docker", "start", container_name])
    
    minutos_vazio = 0
    
    while True:
        try:
            config = carregar_config()
            
            rcon_port = config['rcon']['porta']
            rcon_pass = config['rcon']['senha']
            timeout_max = config['timeout_minutos']
            container_name = config.get('minecraft_nome_container', 'mine-server')
            
            ip_web = config['ip_orange_pi']
            porta_web = config['porta_orange_pi']
            
            jogadores = jogadores_online('127.0.0.1', rcon_port, rcon_pass)
            
            if jogadores >= 0:
                if jogadores == 0:
                    minutos_vazio += 1
                    tempo_restante = timeout_max - minutos_vazio
                    print(f"Servidor vazio. Desligando em {tempo_restante} minutos.")
                    notificar_web(ip_web, porta_web, jogadores, "online", tempo_restante)
                    
                    if minutos_vazio >= timeout_max:
                        print("Timeout atingido! Parando container e desligando...")
                        notificar_web(ip_web, porta_web, 0, "desligando", 0)
                        
                        # Para o container
                        subprocess.run(["docker", "stop", container_name])

                        #Depois verifico se nao vai dar problema. e bom verificar o status dele antes de ir de F

                        # Em seguida, desliga o servidor
                        subprocess.run(["shutdown", "-h", "now"])
                        break
                else:
                    print(f"Jogadores online: {jogadores}")
                    minutos_vazio = 0
                    notificar_web(ip_web, porta_web, jogadores, "online", timeout_max)
            else:
                # Servidor ainda esta iniciando ou offline
                minutos_vazio += 1
                tempo_restante = timeout_max - minutos_vazio
                print(f"Servidor inacessível via RCON. Timeout em {tempo_restante} minutos.")
                notificar_web(ip_web, porta_web, 0, "indisponivel", tempo_restante)
                
                if minutos_vazio >= timeout_max:
                    print("Timeout atingido por falha no RCON! Desligando...")
                    notificar_web(ip_web, porta_web, 0, "desligando", 0)
                    subprocess.run(["docker", "stop", container_name])
                    subprocess.run(["shutdown", "-h", "now"])
                    break
                
        except Exception as e:
            print(f"Erro no loop principal: {e}")
            
        time.sleep(60) # Espera 1 minuto para a proxima checagem

if __name__ == "__main__":
    main()
