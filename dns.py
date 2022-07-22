import socket
from dns_utils import *

port = 53
ip = '127.0.0.1'

if __name__ == '__main__':
    # using ipv4 to send UDP packet
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))

    while True:
        print("Server Up and Running :", f"ip = {ip}", f"port = {port}")
        data, addr = sock.recvfrom(512)
        
        print(data)
        
        dns_response = buildResponse(data)
        sock.sendto(dns_response, addr)