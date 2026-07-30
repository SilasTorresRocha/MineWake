import socket

# O MAC Address do server
mac_address = "00:11:22:33:44:55" #Mudar isso para env ou no painel web depois

# Limpa o endereço MAC e converte para bytes
mac_bytes = bytes.fromhex(mac_address.replace(':', ''))

# Monta a estrutura do Magic Packet: 6 bytes FF seguidos de 16 vezes o MAC
magic_packet = b'\xff' * 6 + mac_bytes * 16

# Cria a conexão de rede local e envia o pacote em formato Broadcast
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(magic_packet, ('255.255.255.255', 9))

print(f"Pacote mágico disparado com sucesso para {mac_address}!")