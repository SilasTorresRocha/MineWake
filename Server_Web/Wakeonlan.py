import socket
import yaml
import os

# No Docker, o arquivo foi montado na mesma pasta (/app)
CONFIG_FILE = 'config_geral.yml'

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)

def enviar_wol():
    config = load_config()
    mac_address = config['minecraft_mac']
    ip_servidor = config.get('ip_server_mine', '192.168.1.20')
    
    # Transforma o IP do servidor
    partes_ip = ip_servidor.split('.')
    partes_ip[3] = '255'
    ip_broadcast = '.'.join(partes_ip)

    # Limpa o endereço MAC e converte para bytes
    mac_bytes = bytes.fromhex(mac_address.replace(':', ''))
    
    # Monta a estrutura do Magic Packet: 6 bytes FF seguidos de 16 vezes o MAC
    magic_packet = b'\xff' * 6 + mac_bytes * 16
    
    # Cria a conexão e envia o pacote direcionado para furar a bolha do Docker
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # Tenta enviar para o IP de Broadcast Direcionado (ex: 192.168.0.255)
        try:
            sock.sendto(magic_packet, (ip_broadcast, 9))
        except Exception:
            pass
            
        # Tenta enviar para o Broadcast Global
        try:
            sock.sendto(magic_packet, ('255.255.255.255', 9))
        except Exception:
            pass
            
        # Tenta enviar diretamente para o IP (funciona se o roteador mantiver o cache ARP)
        try:
            sock.sendto(magic_packet, (ip_servidor, 9))
        except Exception:
            pass
        
    print(f"Pacote mágico disparado com sucesso para {mac_address} via {ip_broadcast} e 255.255.255.255!")
    return True

if __name__ == "__main__":
    enviar_wol()