from session import *
from datetime import datetime, timedelta
import threading
import time
def stream_to_file(stream: ClientStream, filename: str, working_time: int):
    time = datetime.now()
    def work():
        return not stream.is_closed() and (datetime.now() - time) < timedelta(seconds=working_time)

    with open(filename, "wb") as f:
        while work():
            packet = stream.get_message(5)
            if packet:
                f.write(packet.data)

def client_dispatch(session: ClientSession):
    time = datetime.now()
    def work():
        return not session.is_closed and (datetime.now() - time) < timedelta(seconds=120)
    
    while work():
        session.receive_packets(3,3)
        session.send_packets()
    session.close()
    

def file_to_stream(stream: ServerStream, filename: str):
    with open(filename, "rb") as f:
        full_data = f.readlines()
        def work():
            return not stream.is_closed() and len(full_data) > 0
        
        while work():
            stream.process_control_packets()
            data = full_data.pop(0)
            stream.put_data(data)

def server_dispatch(session: ServerSession):
    def work():
        return not session.is_closed
    while work():
        session.receive_packets(3,3)
        for new_stream in session.get_new_streams():
            filename = 'file' + str(new_stream.stream_id) + '.txt'
            threading.Thread(target=file_to_stream, args=(
                new_stream,
                filename,
            ), daemon=True).start()
        session.send_packets()

CLIENT_ADDR = '127.0.0.1'
CLIENT_PORT = 8004
SERVER_ADDR = '127.0.0.1'
SERVER_PORT = 8005


def client_main():
    time.sleep(5)
    client = ClientSession()
    client.connect(CLIENT_ADDR, CLIENT_PORT, SERVER_ADDR, SERVER_PORT)
    stream1 = client.open_new_stream()
    stream2 = client.open_new_stream()
    stream3 = client.open_new_stream()
    thread1 = threading.Thread(target=stream_to_file, args=(stream1, 'worker1.txt',100))
    thread2 = threading.Thread(target=stream_to_file, args=(stream2, 'worker2.txt',100))
    thread3 = threading.Thread(target=stream_to_file, args=(stream3, 'worker3.txt',70))
    
    thread1.start()
    thread2.start()
    thread3.start()
    client_dispatch(client)
    thread1.join()
    thread2.join()
    thread3.join()



def server_main():
    server = ServerSession()
    server.open_socket(SERVER_ADDR, SERVER_PORT)
    server.wait_for_connection()
    server_dispatch(server)
    

def main():
    server_thread = threading.Thread(target=server_main)
    client_thread = threading.Thread(target=client_main)

    client_thread.start()
    server_thread.start()

    client_thread.join()
    server_thread.join()

if __name__ == "__main__":
    main()