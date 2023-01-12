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
import time


class MaximalStreamCountReached(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class StreamNotFound(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidPacket(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidSessionID(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class Session:
    MAX_STREAM_NUMBER = 8
    RESEND_AFTER_TIME = 5
    BUFSIZE = 128
    TIME_BETWEEN_PACKETS = 0.1

    def __init__(self) -> None:
        self.streams = []
        self._socket = None
        self._current_packet_number = 1
        self._unconfirmed_packets = []
        self._parser = Parser()
        self._open = False
        self.closing_procedure = False

    def stream_count(self) -> int:
        return sum(0 if stream.is_closed() else 1 for stream in self.streams)

    def get_active_streams(self) -> List[Stream]:
        return filter(lambda x: not x.is_closed(), self.streams)

    def get_stream(self, stream_id: int) -> Stream:
        for stream in self.get_active_streams():
            if stream.stream_id == stream_id:
                return stream

        raise StreamNotFound

    def _send_packet(self, packet: Packet) -> None:
        if self._open:
            self._socket.send(packet.to_binary())

    def _send_control_packet(self, packet: SessionControlPacket) -> None:
        if self._open:
            packet.packet_number = self._current_packet_number
            self._send_packet(packet)
            self._current_packet_number += 1
            self._unconfirmed_packets.append([packet, datetime.now()])

    def _receive_packet(self, timeout: float = None) -> Packet:
        self._socket.settimeout(timeout)
        if self._open:
            try:
                data = self._socket.recvfrom(Session.BUFSIZE)
                binary_data = data[0]
                return self._parser.parse_packet(binary_data)
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
                time.sleep(Session.TIME_BETWEEN_PACKETS)

    def resend_packets(self) -> None:
        unconfirmed = self._unconfirmed_packets
        self._unconfirmed_packets = []
        for packet_sent_pair in unconfirmed:
            sent = packet_sent_pair[1]
            packet = packet_sent_pair[0]
            if (datetime.now() - sent).total_seconds() >= Session.RESEND_AFTER_TIME:
                self._send_control_packet(packet)
                packet_sent_pair[1] = datetime.now()
                time.sleep(Session.TIME_BETWEEN_PACKETS)

    def close_stream(self, stream_id: int) -> Stream:
        self.get_stream(stream_id).close()

    def _confirm_packet(self, packet_number: int) -> None:
        for i in range(len(self._unconfirmed_packets)):
            unconfirmed = self._unconfirmed_packets[i]
            if unconfirmed[0].packet_number == packet_number:
                del self._unconfirmed_packets[i]
                return

    def _get_max_stream_id(self) -> int:
        return 0 if len(self.streams) == 0 else max(stream.stream_id for stream in self.streams)

    def receive_packets(self, packet_count=10, timeout: float = None) -> None:
        for _ in range(packet_count):
            self.receive_packet(timeout)

    def __del__(self):
        if self._socket is not None:
            self._socket.close()

    def is_open(self):
        return self._open

    def is_closing(self):
        return self.closing_procedure


class ClientSession(Session):
    def __init__(self) -> None:
        super().__init__()

    def open_socket(self, my_address: str, my_port: int, session_id: int = random.randint(0, 32767)):
        self.session_id = session_id
        self.my_address = my_address
        self.my_port = my_port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind((my_address, my_port))

    def connect(self, host_address: str, host_port: int, timeout: float = None) -> None:
        self.host_address = host_address
        self.host_port = host_port
        self._socket.settimeout(timeout)
        self._socket.connect((host_address, host_port))
        opening_packet = SessionControlPacket(
            self.session_id,
            0,
            'o'
        )
        self._open = True
        self.closing_procedure = False
        self._send_control_packet(opening_packet)

    def open_new_stream(self) -> ClientStream:
        if self.stream_count() >= Session.MAX_STREAM_NUMBER:
            raise MaximalStreamCountReached
        stream_id = self._get_max_stream_id() + 1
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

    def receive_packet(self, timeout: float = None) -> None:
        packet = self._receive_packet(timeout)
        if not packet:
            return
        if packet.session_id != self.session_id:
            raise InvalidSessionID
        if isinstance(packet, DataPacket):
            print(
                f"!!!!!!!!!!!!Putting packet number = {packet.packet_number}")
            stream = self.get_stream(packet.stream_id)
            stream.post(packet)
        elif isinstance(packet, ConfirmationPacket):
            self._confirm_packet(packet.packet_number)
        else:
            raise InvalidPacket

    def _close(self, stream_operation, close_type: str) -> None:
        for stream in self.get_active_streams():
            stream_operation(stream)
        closing_packet = SessionControlPacket(
            self.session_id,
            0,
            close_type
        )
        self._send_control_packet(closing_packet)
        self.closing_procedure = True

    def close(self) -> None:
        self._close(lambda stream: stream.close(), 'c')

    def shutdown(self) -> None:
        self._close(lambda stream: stream.shutdown(), 's')


class ServerSession(Session):
    def __init__(self) -> None:
        super().__init__()

    def _confirm(self, packet_number: int) -> None:
        confirmation_packet = ConfirmationPacket(
            self.session_id,
            packet_number,
            0,
        )
        self._send_packet(confirmation_packet)

    def open_socket(self, my_address: str, my_port: int) -> None:
        self.my_address = my_address
        self.my_port = my_port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind((my_address, my_port))

    def wait_for_connection(self, timeout: float = None) -> None:
        correct = False
        while not correct:
            self._socket.settimeout(timeout)
            data = self._socket.recvfrom(Session.BUFSIZE)
            host_info = data[1]
            packet = self._parser.parse_packet(data[0])
            if isinstance(packet, SessionControlPacket) and packet.control_type == 'o':
                self.session_id = packet.session_id
                self._socket.connect(host_info)
                self._open = True
                self.closing_procedure = False
                self._confirm(packet.packet_number)
                self.host_address = host_info[0]
                self.host_port = host_info[1]
                correct = True

    def receive_packet(self, timeout: float = None) -> None:
        packet = self._receive_packet(timeout)
        if not packet:
            return
        if packet.session_id != self.session_id:
            raise InvalidSessionID
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
                    new_stream = ServerStream(
                        self.session_id, packet.stream_id)
                    new_stream.new = True
                    self.streams.append(new_stream)
            else:
                stream = self.get_stream(packet.stream_id)
                stream.close()
            self._confirm(packet.packet_number)

        elif isinstance(packet, RetransmissionRequestPacket):
            stream = self.get_stream(packet.stream_id)
            stream.post(packet)
        else:
            raise InvalidPacket

    def get_new_streams(self) -> List[ServerStream]:
        streams = list(filter(lambda x: x.new, self.get_active_streams()))

        for stream in streams:
            stream.new = False
        return streams

    def _close(self, stream_operation) -> None:
        for stream in self.get_active_streams():
            stream_operation(stream)
        self.closing_procedure = True

    def close(self) -> None:
        self._close(lambda stream: stream.close())

    def shutdown(self) -> None:
        self._close(lambda stream: stream.shutdown())
