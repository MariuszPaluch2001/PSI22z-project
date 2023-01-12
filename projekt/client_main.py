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

CLIENT_ADDR = '127.0.0.1'
CLIENT_PORT = 8004
SERVER_ADDR = '127.0.0.1'
SERVER_PORT = 8005
CLIENT_WORK = 120


def stream_to_file(stream: ClientStream, filename: str, working_time: int):
    time = datetime.now()
    # strumień klienta pracuje dopóki nie minie założony czas
    #  lub nie zostanie zamknięty
    print(f'Strumień klienta z id: {stream.stream_id} rozpoczyna działanie')

    def work():
        return not stream.is_closed() and \
            (datetime.now() - time) < timedelta(seconds=working_time)
    f_text = open(filename, 'wb')
    f_stamped = open(filename + '.stamped', 'wb')
    while work():
        # klient oczekuje maksymalnie 1 sekundę na nową, poprawną wiadomość
        if packet := stream.get_message(1):
            # pisanie do pliku znakowanego i do pliku tekstowego
            f_text.write(packet.data)
            f_text.flush()
            f_stamped.write(str(packet.timestamp).encode('ascii'))
            f_stamped.write(packet.data)
            f_stamped.flush()
    print(f'Strumień klienta z id: {stream.stream_id} kończy działanie')
    f_text.close()
    f_stamped.close()


def client_dispatch(session: ClientSession):
    time = datetime.now()

    # klient pracuje przez 200 sekund lub do zamknięcia
    def work():
        return not session.is_closing() and \
            (datetime.now() - time) < timedelta(seconds=CLIENT_WORK)

    while work():
        # klient odbiera do 5 paczek z timeoutem = 1s
        session.receive_packets(5, 1)
        # klient rozsyła paczki kontrolne, niepotwierdzone paczki
        # i paczki wzięte od strumieni
        session.send_packets()
    print('Sesja klienta kończy pracę')
    session.close()



def client_main():
    # klienta czeka na ustawienie serwera
    time.sleep(1)
    client = ClientSession()
    print('Sesja klienta rozpoczęta - próba połączenia z serwerem')
    client.open_socket(CLIENT_ADDR, CLIENT_PORT)
    client.connect(SERVER_ADDR, SERVER_PORT)
    print('Klientowi udało się połączyć z serwerem')
    # tworzymy wątki dla strumieni klienta - z różnym czasem życia
    threads = [
        threading.Thread(target=stream_to_file, args=(
            client.open_new_stream(),
            'worker' + str(i) + '.txt',
            random.randint(CLIENT_WORK-40, CLIENT_WORK+40)
        ))
        for i in range(1, 9)
    ]
    for thread in threads:
        thread.start()
    client_dispatch(client)
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    client_main()
