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
from typing import List
from datetime import datetime
import socket
#sprawdzanie id sesji i korekcja
#może diagnostycznie - co kilkanaście sekund trzeba potwierdzenia przesyłu?
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
    RESEND_AFTER_TIME = 5
    BUFSIZE = 128

    def __init__(self) -> None:
        self.streams = []
        self.socket = None
        self.current_packet_number = 1
        self.unconfirmed_packets = []
        self.parser = Parser()
        self.is_open = False
    

    def stream_count(self) -> int:
        return sum(0 if stream.is_closed() else 1 for stream in self.streams)

    def get_active_streams(self) -> List[Stream]:
        return filter(lambda x : not x.is_closed(), self.streams)

    def get_stream(self, stream_id: int) -> Stream:
        for stream in self.get_active_streams():
            if stream.stream_id == stream_id:
                return stream

        raise StreamNotFound

    def _send_packet(self, packet: Packet) -> None:
        if self.is_open:
            self.socket.send(packet.to_binary())

    def _send_control_packet(self, packet: SessionControlPacket) -> None:
        if self.is_open:
            packet.packet_number = self.current_packet_number
            self._send_packet(packet)
            self.current_packet_number = self.current_packet_number + 1
            self.unconfirmed_packets.append([packet,datetime.now()])

    def _receive_packet(self, timeout=None) -> Packet:
        self.socket.settimeout(timeout)
        if self.is_open:
            try:
                data = self.socket.recvfrom(Session.BUFSIZE)
                binary_data = data[0]
                return self.parser.parse_packet(binary_data)
            except:
                return 
    def send_packets(self):
        self.resend_packets()
        for stream in self.get_active_streams():            
            if len(stream.message_buffer_out) > 0:
                packet = stream.get_packet()
                if isinstance(packet, RetransmissionRequestPacket):
                    self._send_control_packet(packet)
                else:
                    self._send_packet(packet)

    def resend_packets(self) -> None:
        unconfirmed = self.unconfirmed_packets
        self.unconfirmed_packets = []
        for packet_sent_pair in unconfirmed:
            sent = packet_sent_pair[1]
            packet = packet_sent_pair[0]
            if (datetime.now() - sent).total_seconds() >= Session.RESEND_AFTER_TIME:
                self._send_control_packet(packet)
                packet_sent_pair[1] = datetime.now()
                      

    def close_stream(self,stream_id: int) -> Stream:
        self.get_stream(stream_id).close()

    def confirm_packet(self,packet_number: int) -> None:
        for i in range(len(self.unconfirmed_packets)):
            unconfirmed = self.unconfirmed_packets[i]
            if unconfirmed[0].packet_number == packet_number:
                del self.unconfirmed_packets[i]
                return

    def get_max_stream_id(self) -> int:
        return 0 if len(self.streams) == 0 else max(stream.stream_id for stream in self.streams)

    def receive_packets(self, packet_count=10,timeout=None) -> None:
        for _ in range(packet_count):
            self.receive_packet(timeout)

    def __del__(self):
        if self.socket is not None:
            self.socket.close() 
class ClientSession(Session):
    def __init__(self) -> None:
        super().__init__()

    #change to 2 functions maybe
    def connect(self, my_address: str, my_port: int,
     host_address: str, host_port: int, session_id: int = random.randint(0,32767)) -> None:
        self.session_id = session_id
        self.my_address = my_address
        self.my_port = my_port
        self.host_address = host_address
        self.host_port = host_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((my_address, my_port))
        self.socket.connect((host_address, host_port))
        opening_packet = SessionControlPacket(
            self.session_id,
            0,
            'o'
        )
        self.is_open = True
        self.is_closed = False
        self._send_control_packet(opening_packet)


    def open_new_stream(self) -> ClientStream:
        if self.stream_count() >= Session.MAX_STREAM_NUMBER:
            raise MaximalStreamCountReached
        stream_id = self.get_max_stream_id() + 1
        stream_opening_packet = StreamControlPacket(
            self.session_id,
            0,
            'o',
            stream_id
        )
        self._send_control_packet(stream_opening_packet)
        stream = ClientStream(stream_id, self.session_id)  
        self.streams.append(stream)
        return stream      
    
    def receive_packet(self,timeout=None) -> None:
        packet = self._receive_packet(timeout)
        if not packet:
            return 
        if isinstance(packet, DataPacket):
            print(f"!!!!!!!!!!!!Putting packet number = {packet.packet_number}")
            stream = self.get_stream(packet.stream_id)
            stream.post(packet)
        elif isinstance(packet, ConfirmationPacket):
            self.confirm_packet(packet.packet_number)
        else:
            raise InvalidPacket



    def _close(self, stream_operation, close_type : str) -> None:
        for stream in self.get_active_streams():
            stream_operation(stream)
        closing_packet = SessionControlPacket(
            self.session_id,
            0,
            close_type
        )
        self._send_control_packet(closing_packet)
        self.is_closed = True

    def close(self) -> None:
        self._close(lambda stream : stream.close(), 'c')
     
    def shutdown(self) -> None:
        self._close(lambda stream : stream.shutdown(), 's')


class ServerSession(Session):
    def __init__(self) -> None:
        super().__init__()

    def confirm(self, packet_number:int) -> None:
        confirmation_packet = ConfirmationPacket(
            self.session_id,
            packet_number,
            0,
        )
        self._send_packet(confirmation_packet)

    def open_socket(self, my_address: str, my_port: int) -> None:
        self.my_address = my_address
        self.my_port = my_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((my_address, my_port))

    def wait_for_connection(self) -> None:
        correct = False
        while not correct:
            data = self.socket.recvfrom(Session.BUFSIZE)
            host_info = data[1]
            packet = self.parser.parse_packet(data[0])
            if isinstance(packet, SessionControlPacket) and packet.control_type == 'o':
                self.session_id = packet.session_id
                self.socket.connect(host_info)
                self.is_open = True
                self.is_closed = False
                self.confirm(packet.packet_number)
                self.host_address = host_info[0]
                self.host_port = host_info[1]
                correct = True


    def receive_packet(self, timeout=None) -> None:
        packet = self._receive_packet(timeout)
        if not packet:
            return
        if isinstance(packet, SessionControlPacket):
            if packet.control_type == 'c':
                self.close()
            elif packet.control_type == 's':
                self.shutdown()
            elif packet.control_type == 'o':
                pass
        elif isinstance(packet, StreamControlPacket):
            if packet.control_type == 'o':
                if self.stream_count() < Session.MAX_STREAM_NUMBER:
                    new_stream = ServerStream(self.session_id, packet.stream_id)
                    new_stream.new = True
                    self.streams.append(new_stream)
            else:
                stream = self.get_stream(packet.stream_id)
                stream.close()
            self.confirm(packet.packet_number)
  
        elif isinstance(packet,RetransmissionRequestPacket):
            stream = self.get_stream(packet.stream_id)
            stream.post(packet)
        else:
            raise InvalidPacket

    def get_new_streams(self) -> List[ServerStream]:
        streams = list(filter(lambda x : x.new, self.get_active_streams()))

        for stream in streams:
            stream.new = False
        return streams


    def _close(self, stream_operation) -> None:
        for stream in self.get_active_streams():
            stream_operation(stream)
        self.is_closed = True

    def close(self) -> None:
        self._close(lambda stream : stream.close())
     
    def shutdown(self) -> None:
        self._close(lambda stream : stream.shutdown())
