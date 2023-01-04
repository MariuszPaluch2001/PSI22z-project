import server_main
from packets import RetransmissionRequestPacket
import socket
import threading
import time
def fake_server():
    #serwer nigdy nie powinien prosić o retransmisję, a tutaj wysyła prośbę
    packet = RetransmissionRequestPacket(1,1,1,1)
    with socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) as s:
        s.bind((server_main.SERVER_ADDR, server_main.SERVER_PORT))
        time.sleep(10)
        s.connect((server_main.CLIENT_ADDR, server_main.CLIENT_PORT))
        s.send(packet.to_binary())
        
    

def main():
    client_thread = threading.Thread(target=server_main.client_main)
    fake_server_thread = threading.Thread(target=fake_server)
    client_thread.start()
    fake_server_thread.start()

    client_thread.join()
    fake_server_thread.join()


if __name__ == "__main__":
    main()


