from Parser import Parser
from stream import ClientStream, ServerStream, Stream
from packets import (
    SessionControlPacket,
    StreamControlPacket,
    ConfirmationPacket,
    DataPacket,
    RetransmissionRequestPacket,
    Packet
)
import random
from typing import (List,Tuple)

class MaximalStreamCountReached(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class StreamNotFound(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class InvalidPacket(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class Session:
    MAX_STREAM_NUMBER = 8
    def __init__(self) -> None:
        self.streams = []
        self.socket = None
        self.current_packet_number = 1
        self.unconfirmed_packets = []

    def stream_count(self) -> int:
        return sum(0 if stream.is_closed() else 1 for stream in self.streams)

    def get_active_streams(self) -> List[Stream]:
        return filter(lambda x : not x.is_closed(), self.streams)

    def get_stream(self, stream_id: int) -> Stream:
        for stream in self.get_active_streams():
            if stream.stream_id == stream_id:
                return stream

        raise StreamNotFound

    def close(self) -> None:
        ...

    def shutdown(self) -> None:
        ...

    def _send_packet(self, packet: Packet) -> None:
        ...

    def _receive_packet(self) -> Packet:
        ...

    def send_packets(self) -> Stream:
        self.resend_packets()
        for stream in self.get_active_streams():
            #@todo - it will be changed queue and mutexes!!
            if len(stream.message_buffer_out) > 0:
                self._send_packet(stream.message_buffer_out.pop(0))

    def resend_packets(self) -> None:
        ...
        
    def close_stream(self,stream_id: int) -> Stream:
        self.get_stream(stream_id).close()

    def confirm_message(self,packet_number: int) -> None:
        ...

class ClientSession(Session):
    def __init__(self) -> None:
        super().__init__()

    def connect(self, my_address: int, my_port: int, host_address: int, host_port: int) -> None:
        self.session_id = random.randint(0,32767)
        self.my_address = my_address
        self.my_port = my_port
        self.host_address = host_address
        self.host_port = host_port
        ...

    def open_new_stream(self) -> ClientStream:
        if self.stream_count() >= Session.MAX_STREAM_NUMBER:
            raise MaximalStreamCountReached
        ...
    
    def receive_packets(self, packet_count=10) -> None:
        for _ in range(packet_count):
            packet = self._receive_packet()
            if isinstance(packet, SessionControlPacket):
                ...
            elif isinstance(packet, DataPacket)  or isinstance(packet, RetransmissionRequestPacket):
                stream = self.get_stream(packet.stream_id)
                stream.message_buffer_in.append(packet)
            elif isinstance(packet, ConfirmationPacket):
                if packet.stream_id == 0:
                    ...
                else:
                    stream = self.get_stream(packet.stream_id)
                    stream.message_buffer_in.append(packet)
            else:
                raise InvalidPacket

class ServerSession(Session):
    def __init__(self) -> None:
        super().__init__()

    def wait_for_connection(self, my_address: int, my_port: int) -> None:
        ...

    def receive_packets(self, packet_count=10) -> None:
        ...

    def get_new_streams(self) -> List[ServerStream]:
        ...



