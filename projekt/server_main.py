from session import (
    ClientSession,
    ClientStream,
    ServerSession,
    ServerStream
)
from datetime import datetime, timedelta
import threading
import time
import random

SERVER_ADDR = '127.0.0.1'
SERVER_PORT = 8005

def file_to_stream(stream: ServerStream, filename: str):
    print(f'Strumień serwera z id: {stream.stream_id} rozpoczyna pracę')
    with open(filename, "rb") as f:
        full_data = f.readlines()

        # praca aż do zamknięcia lub wykonania zadania
        def work():
            return not stream.is_closed()

        while work():
            # strumień serwera procesuje paczki kontrolne
            stream.process_control_packets()
            # strumień serwera wysyła porcję danych
            if len(full_data) > 0:
                data = full_data.pop(0)
                stream.put_data(data)
            # spanie do demonstracji działania znakowania czasowego
            time.sleep(1)
    print(f'Strumień serwera z id: {stream.stream_id} kończy pracę')


def server_dispatch(session: ServerSession):
    def work():
        return not session.is_closing()
    while work():
        # serwer oczekuje na maks. 5 paczek z timeoutem=1s
        session.receive_packets(5, 1)
        # gdy serwer dostanie polecenie otwarcia strumienia, to tworzy go
        # i przydziela mu pracę w nowym wątku
        for new_stream in session.get_new_streams():
            filename = 'file' + str(new_stream.stream_id)
            threading.Thread(target=file_to_stream, args=(
                new_stream,
                filename,
            ), daemon=True).start()
        # serwer wysyła pakiety odebrane od strumieni oraz potwierdzenia paczek
        session.send_packets()
    print('Sesja serwera kończy pracę')


def server_main():
    server = ServerSession()
    print('otwarcie sesji serwera - oczekiwanie na połaczenie')
    server.open_socket(SERVER_ADDR, SERVER_PORT)
    server.wait_for_connection()
    print('sesja serwera otrzymała połączenie od klienta')
    server_dispatch(server)


if __name__ == "__main__":
    server_main()
