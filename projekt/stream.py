import queue
from threading import Thread, Condition
from packets import *
from typing import List

class Stream:
    #ważne, żebyś dodał pisanie do loggera - jest to potrzebne na prezentację
    def __init__(self,session_id,stream_id,logger=None) -> None:
        self.stream_id = stream_id
        self.session_id = session_id
        self.logger = logger
        self.message_buffer_in = queue.PriorityQueue()
        self.message_buffer_out = []

        self.closed = False
        self.data_packet_number = 1

    def is_closed(self):
        return self.closed

    def close(self):
        self.closed = True

    def shutdown(self):
        self.closed = True

    def _put_packet(self, packet: Packet) -> None:
        if not self.closed:
            #tutaj np. mutex
            self.message_buffer_out.append(packet)

    def _get_packet(self, timeout=None) -> Packet:
        #musisz dodać jakieś mądre czekanie
        if not self.closed:
            #mutex
            try:
                print(self.message_buffer_in.queue)
                return self.message_buffer_in.get(block = True, timeout=timeout)[1]
            except queue.Empty:
                pass

class ClientStream(Stream):
    def __init__(self, stream_id, session_id, logger=None) -> None:
        super().__init__(session_id,stream_id,logger)
        self.condition = Condition()
    
    def post(self, data):
        with self.condition:
            self.message_buffer_in.put(data)
            self.condition.notify()

    def get_message(self,timeout=None) -> DataPacket:
        message = self._get_packet(timeout)
        if message is None:
            return

        while (message.packet_number != self.data_packet_number):
            self.message_buffer_in.put((message.packet_number, message))
            self._request_retransmission(self.data_packet_number)

            with self.condition:
                self.condition.wait()
                message = self._get_packet(timeout)

        self.data_packet_number += 1
        return message

    def get_all_messages(self) -> List[Packet]:
        messages = []
        next = self.data_packet_number
        
        message = self._get_packet(0)
        while(message):
            if message.packet_number == next:
                messages.append(message)
                next +=1
            else:
                self.message_buffer_in.put((message.packet_number, message))
                self.data_packet_number = next
                break

            message = self._get_packet(0)

        return messages
        #tutaj zwracasz tak długi ciąg nagłówków, jaki możez osiągnąć bez czekania na nic


    def _close(self, super_operation, closing_type) -> None:
        
        closing_packet = StreamControlPacket(
            self.session_id,
            0,
            closing_type
        )
        self._put_packet(closing_packet)
        super_operation(super())
    
    def close(self) -> None:
        self._close(lambda x : x.close(), 'c')

    def shutdown(self):
        self._close(lambda x : x.shutdown(), 's')

    def _request_retransmission(self, packet_number):
        retransmission_packet = RetransmissionRequestPacket(
            self.session_id,
            packet_number,
            'o', #tutaj jest błędna dana - ona potem wyleci
            self.stream_id
        )
        self._put_packet(retransmission_packet)

    
class ServerStream(Stream):
    def __init__(self, stream_id, logger=None) -> None:
        super().__init__(stream_id, logger)
        self.new = True
        self.data_packets = []

    def process_control_packets(self):
        #tutaj obsługujesz 2 typy pakietów
        #1. retransmisja - szukasz w data_packets, tego, czego brakuje
        #2. zamknięcie - wywołujesz self.close() albo shutdown()
        ...

    def put_data(self, data) -> None:
        #tutaj dzielisz na pakiety i dodajesz je do self.data_packets
        #wrzucasz je też do wysyłki
        ...

