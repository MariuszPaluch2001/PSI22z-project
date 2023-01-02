from packets import *
from typing import List
class Stream:
    def __init__(self,session_id,stream_id,logger=None) -> None:
        self.stream_id = stream_id
        self.session_id = session_id
        self.logger = logger
        #Kolejki - kolejki priorytetowe ?
        self.message_buffer_in = []
        self.message_buffer_out = []

        self.closed = False
        self.data_packet_number = 1
        self.other_packet_number = 1

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
            if len(self.message_buffer_in) > 0:
                return self.message_buffer_in.pop(0)



class ClientStream(Stream):
    def __init__(self, stream_id, session_id, logger=None) -> None:
        super().__init__(session_id,stream_id,logger)

    def get_message(self,timeout=None) -> None:
        ...
        #tutaj musisz zrobić 3 rzeczy
        #1.czekanie na wiadomość jak nie ma nowego komunikatu
        #2.jak są komunikaty, ale za duży packet number, to wysyłasz retranmisje
        # z numerem nagłówka, na jaki czekasz i też czekasz z timeoutem
        #3. jak jest ten, który chcemy, to go zwraczasz
    

    def get_all_messages(self) -> List[Packet]:
        ...
        #tutaj zwracasz tak długi ciąg nagłówków, jaki możez osiągnąć bez czekania na nic
        

    def _close(self, super_operation, closing_type) -> None:
        
        closing_packet = StreamControlPacket(
            self.session_id,
            self.other_packet_number,
            closing_type
        )
        self._put_packet(closing_packet)
        self.other_packet_number = self.other_packet_number + 1
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
        self.data = []

    def process_control_packets(self):
        ...

    