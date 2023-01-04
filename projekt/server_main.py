from session import *
from datetime import datetime, timedelta
import threading
import time

CLIENT_ADDR = '127.0.0.1'
CLIENT_PORT = 8004
SERVER_ADDR = '127.0.0.1'
SERVER_PORT = 8005
CLIENT_WORK = 120

def stream_to_file(stream: ClientStream, filename: str, working_time: int):
    time = datetime.now()
    #strumień klienta pracuje dopóki nie minie założony czas lub nie zostanie zamknięty
    print('Strumień klienta rozpoczyna działanie')
    def work():
        return not stream.is_closed() and (datetime.now() - time) < timedelta(seconds=working_time)
    f_text = open(filename, 'wb')
    f_stamped = open(filename + '.stamped', 'wb')
    while work():
        #klient oczekuje maksymalnie 1 sekundę na nową, poprawną wiadomość
        if packet := stream.get_message(1):
            #pisanie do pliku znakowanego i do pliku tekstowego
            f_text.write(packet.data)
            f_stamped.write(str(packet.timestamp).encode('ascii'))
            f_stamped.write(packet.data)
    print('Strumień klienta kończy działanie')
    f_text.close()
    f_stamped.close()

def client_dispatch(session: ClientSession):
    time = datetime.now()
    #klient pracuje przez 200 sekund lub do zamknięcia
    def work():
        return not session.is_closed and (datetime.now() - time) < timedelta(seconds=CLIENT_WORK)
    
    while work():
        #klient odbiera do 5 paczek z timeoutem = 1s
        session.receive_packets(5,1)
        #klient rozsyła paczki kontrolne, niepotwierdzone paczki i paczki wzięte od strumieni
        session.send_packets()
    print('Sesja klienta kończy pracę')
    session.close()
    
    

def file_to_stream(stream: ServerStream, filename: str):
    print('Strumień serwera rozpoczyna pracę')
    with open(filename, "rb") as f:
        full_data = f.readlines()
        #praca aż do zamknięcia lub wykonania zadania
        def work():
            return not stream.is_closed() and len(full_data) > 0
        
        while work():
            #strumień serwera procesuje paczki kontrolne
            stream.process_control_packets()
            #strumień serwera wysyła porcję danych
            data = full_data.pop(0)
            stream.put_data(data)
            #spanie do demonstracji działania znakowania czasowego
            time.sleep(1)
    print('Strumień klienta kończy pracę')

def server_dispatch(session: ServerSession):
    def work():
        return not session.is_closed
    while work():
        #serwer oczekuje na maks. 5 paczek z timeoutem=1s
        session.receive_packets(5,1)
        #gdy serwer dostanie polecenie otwarcia strumienia, to tworzy go
        #i przydziela mu pracę w nowym wątku
        for new_stream in session.get_new_streams():
            filename = 'file' + str(new_stream.stream_id)
            threading.Thread(target=file_to_stream, args=(
                new_stream,
                filename,
            ), daemon=True).start()
        #serwer wysyła pakiety odebrane od strumieni oraz potwierdzenia paczek
        session.send_packets()
    print('Sesja serwera kończy pracę')




def client_main():
    #klienta czeka na ustawienie serwera
    time.sleep(5)
    client = ClientSession()
    print('Sesja klienta rozpoczęta - próba połączenia z serwerem')
    client.connect(CLIENT_ADDR, CLIENT_PORT, SERVER_ADDR, SERVER_PORT)
    print('Klientowi udało się połączyć z serwerem')
    #tworzymy wątki dla strumieni klienta - z różnym czasem życia
    threads = [
        threading.Thread(target=stream_to_file, args=(
            client.open_new_stream(),
            'worker' + str(i) + '.txt', 
            random.randint(CLIENT_WORK-40, CLIENT_WORK+40)
        ))
        for i in range(1,9)
    ]
    for thread in threads:
        thread.start()
    client_dispatch(client)
    for thread in threads:
        thread.join()
    


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