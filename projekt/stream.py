# STRumyk, Mariusz Paluch
# Plik zawiera definicje klas stream dla klienta i serwera. Zadaniem tych klas jest
# obsługa strumieni w ramach sesji. Dodatkowo w ramach debugowania znajduje się również
# własna implementacja Loggera.


import io
from queue import PriorityQueue, Empty
from threading import Condition, Lock
from packets import *
from typing import List


class Logger:
    def __init__(self) -> None:
        pass

    def write_packet_log(self, func_name: str, packet: Packet):
        if isinstance(packet, RetransmissionRequestPacket):
            print(f'{func_name}: stream_id={packet.stream_id} session_id={packet.session_id} '
                  f'number={packet.packet_number} retr={packet.requested_packet_number} type=RetransmissionRequestPacket')
        else:
            print(f'{func_name}: stream_id={packet.stream_id} session_id={packet.session_id} '
                  f'number={packet.packet_number} type=DataPacket')

    def write_log(self, func_name: str, message: str):
        print(f"!!!{func_name}: {message}")


class Stream:
    def __init__(self, session_id, stream_id, logger=None) -> None:
        self.stream_id = stream_id
        self.session_id = session_id
        self.logger = logger
        self.message_buffer_in = PriorityQueue()
        self.message_buffer_out = []

        self.closed = False
        self.data_packet_number = 1

        self.mutex_in = Lock()
        self.mutex_out = Lock()

        self.condition = Condition()

    def is_closed(self):
        return self.closed

    def close(self):
        self.closed = True

    def shutdown(self):
        self.closed = True

    def _upload_packet(self, packet):
        raise NotImplementedError

    def upload_packet(self, packet: Packet):
        """
            Funkcja odpowiedzialna za wrzucanie do kolejki wejściowej pakietów.
            Różne implementacje dla klienta i serwera. Flaga zwracana
            przez funkcję informuje zmienną warunkową o potrzebie wybudzenia
            czekającego wątku.
        """
        self.mutex_in.acquire()
        try:
            flag = self._upload_packet(packet)
        finally:
            self.mutex_in.release()
        return flag

    def send(self, packet: Packet) -> None:
        """
            Funkcja wstawiająca do bufora wyjściowego pakiety.
            Dla klienta są to prośby o zamknięcie, oraz RetransmissionRequestPacket;
            Dla serwera są to DataPackets.
        """
        if not self.closed:
            self.mutex_out.acquire()
            try:
                if self.logger is not None:
                    self.logger.write_packet_log("send", packet)
                self.message_buffer_out.append(packet)
            finally:
                self.mutex_out.release()

    def get_packet(self):
        """
            Pobiera komunikat, który nadaje się do wysyłki siecią.
        """
        self.mutex_out.acquire()
        try:
            message = self.message_buffer_out.pop(0)
            if self.logger is not None:
                self.logger.write_packet_log("get_packet", message)
        finally:
            self.mutex_out.release()

        return message

    def _recv(self, timeout=None) -> Packet:
        """
            Pobiera jeden komunikat z kolejki wejściowej.
        """
        if not self.closed:
            try:
                packet = self.message_buffer_in.get(
                    block=True, timeout=timeout)[1]
                if self.logger is not None:
                    self.logger.write_packet_log("_recv", packet)
                return packet
            except Empty:
                pass

    def post(self, packet: Packet):
        """
            Funkcja wołana z zewnątrz, aby dołożyć odebrany komunikat do kolejki wejściowej.
            Dla kienta to będą komunikaty DataPacket, a dla serwera StreamControlPacket i
            RetransmissionRequestPacket.
        """
        with self.condition:
            if self.logger is not None:
                self.logger.write_packet_log("post", packet)
            if self.upload_packet(packet):
                self.condition.notify()


class ClientStream(Stream):
    def __init__(self, stream_id, session_id) -> None:
        super().__init__(session_id, stream_id)

    def _upload_packet(self, packet: DataPacket):
        if self.logger is not None:
            self.logger.write_packet_log("client_upload_packet", packet)

        # sprawdzanie czy już nie przetworzyliśmy tego komunikatu
        if self.data_packet_number <= packet.packet_number:
            # sprawdza czy taki pakiet nie jest już w buforze
            if packet.packet_number not in map(lambda x: x[0], self.message_buffer_in.queue):
                self.message_buffer_in.put(
                    (packet.packet_number, packet))

            # odebrano komunikat na który czeka wątek klienta
            if self.data_packet_number == packet.packet_number:
                return True

        return False

    def get_message(self, timeout=None) -> DataPacket:
        """
            Funkcja której celem jest przeczytać wiadomość o odpowiednim
            numerze. Jeśli nie ma takiej wiadmości, to wysyłana jest do serwera
            prośba o retransmisję.
        """
        message = self._recv(timeout)
        if message is None:
            return

        while (message.packet_number != self.data_packet_number):
            if self.logger is not None:
                self.logger.write_log("get_message", f'Client received message with packet number '
                                      f'{message.packet_number} waiting for packet {self.data_packet_number}')
            self.upload_packet(message)  # odkładanie wiadomości do kolejki
            self._request_retransmission(self.data_packet_number)

            with self.condition:
                self.condition.wait()
                message = self._recv(timeout)

        self.data_packet_number += 1
        return message

    def get_all_messages(self) -> List[Packet]:
        """
            Funkcja której celem jest odczytania jak najdłuższego ciągu wiadomości
            z bufora o prawidłowych numerach.
        """
        messages = []
        next = self.data_packet_number

        message = self._recv(0)
        while (message):
            if message.packet_number == next:
                messages.append(message)
                next += 1
            else:
                # odkładanie wiadomości o niewłaściwym numerze
                self.upload_packet(message)
                self.data_packet_number = next
                break

            message = self._recv(0)

        return messages

    def _close(self, super_operation, closing_type) -> None:

        closing_packet = StreamControlPacket(
            self.session_id,
            0,
            closing_type,
            self.stream_id
        )
        self.send(closing_packet)
        super_operation(super())

    def close(self) -> None:
        self._close(lambda x: x.close(), 'c')

    def shutdown(self):
        self._close(lambda x: x.shutdown(), 's')

    def _request_retransmission(self, packet_number):
        retransmission_packet = RetransmissionRequestPacket(
            self.session_id,
            0,  # pole uzupełniane przez session
            self.stream_id,
            packet_number
        )
        self.send(retransmission_packet)


class ServerStream(Stream):
    def __init__(self, session_id, stream_id) -> None:
        super().__init__(session_id, stream_id)
        self.new = True
        self.data_packets = []
        self.data_packet_number_to_send = 1

    def _upload_packet(self, packet: RetransmissionRequestPacket):
        """
            Funkcja implementująca upload_packet dla serwera.
            Otrzymuje ona zawsze prośbę o retransmisję. Nie ma ryzyka
            otrzymania tutaj złych danych, a więc pakiet jest od razu
            wrzucany do kolejki.
        """
        if self.logger is not None:
            self.logger.write_packet_log("server_upload_packet", packet)

        self.message_buffer_in.put(
            (packet.packet_number, packet))
        return True

    def _process_one_control_packet(self, packet: RetransmissionRequestPacket):
        """
            Funkcja szukająca w buforze pakietu o takim samym numerze
            jak w retransmisji.
        """
        for data_packet in self.data_packets:
            if data_packet.packet_number == packet.requested_packet_number:
                self.send(data_packet)

    def process_control_packets(self):
        """
            Funkcja obsługująca prośby o retransmisję pakietów.
        """
        packet = self._recv(0)
        while (packet):
            self._process_one_control_packet(packet)
            packet = self._recv(0)

    def put_data(self, data: bytes) -> None:
        """
            Funkcja czytająca dane ze strumienia, odpowiednio dzieli dane, 
            i tworzy dla każdej porcji osobny pakiet.
        """
        data_stream = io.BytesIO(data)
        while True:
            data_chunk = data_stream.read(100)
            if not data_chunk:
                break
            packet = DataPacket(
                self.session_id,
                self.data_packet_number_to_send,
                self.stream_id,
                bytearray(data_chunk)
            )
            self.data_packets.append(
                packet
            )

            if self.data_packet_number_to_send % 2 == 1:  # ACHTUNG! tylko do testów. Potem wywalić
                self.send(packet)

            self.data_packet_number_to_send += 1
