from queue import PriorityQueue, Empty
from threading import Condition, Lock
import io
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
    # ważne, żebyś dodał pisanie do loggera - jest to potrzebne na prezentację
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

    def _upload_packet(self, message):
        raise NotImplementedError

    def upload_packet(self, message: Packet):
        self.mutex_in.acquire()
        try:
            flag = self._upload_packet(message)
        finally:
            self.mutex_in.release()
        return flag

    def send(self, packet: Packet) -> None:
        if not self.closed:
            self.mutex_out.acquire()
            try:
                if self.logger is not None:
                    self.logger.write_packet_log("send", packet)
                self.message_buffer_out.append(packet)
            finally:
                self.mutex_out.release()

    def get_packet(self):
        self.mutex_out.acquire()
        try:
            message = self.message_buffer_out.pop(0)
            if self.logger is not None:
                self.logger.write_packet_log("get_packet", message)
        finally:
            self.mutex_out.release()

        return message

    def _recv(self, timeout=None) -> Packet:
        if not self.closed:
            try:
                packet = self.message_buffer_in.get(
                    block=True, timeout=timeout)[1]
                if self.logger is not None:
                    self.logger.write_packet_log("_recv", packet)
                return packet
            except Empty:
                pass

    def post(self, data):
        with self.condition:
            if self.logger is not None:
                self.logger.write_packet_log("post", data)
            if self.upload_packet(data):
                self.condition.notify()


class ClientStream(Stream):
    def __init__(self, stream_id, session_id) -> None:
        super().__init__(session_id, stream_id)

    def _upload_packet(self, message):
        if self.logger is not None:
            self.logger.write_packet_log("upload_packet", message)

        flag = False
        if self.data_packet_number <= message.packet_number:
            if message.packet_number in map(lambda x: x[0], self.message_buffer_in.queue):
                flag = False
            else:
                self.message_buffer_in.put(
                    (message.packet_number, message))

        if self.data_packet_number == message.packet_number:
            flag = True
        
        return flag

    def get_message(self, timeout=None) -> DataPacket:
        message = self._recv(timeout)
        if message is None:
            return

        while (message.packet_number != self.data_packet_number):
            if self.logger is not None:
                self.logger.write_log("get_message", f'Client received message with packet number '
                                      f'{message.packet_number} waiting for packet {self.data_packet_number}')
            self.message_buffer_in.put((message.packet_number, message))
            self._request_retransmission(self.data_packet_number)

            with self.condition:
                self.condition.wait()
                message = self._recv(timeout)

        self.data_packet_number += 1
        return message

    def get_all_messages(self) -> List[Packet]:
        messages = []
        next = self.data_packet_number

        message = self._recv(0)
        while (message):
            if message.packet_number == next:
                messages.append(message)
                next += 1
            else:
                self.message_buffer_in.put((message.packet_number, message))
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
            0,
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

    def _upload_packet(self, message):
        if self.logger is not None:
            self.logger.write_packet_log("upload_packet", message)
        
        self.message_buffer_in.put(
                    (message.packet_number, message))
        return True
        
    def _process_one_control_packet(self, packet):
        for data_packet in self.data_packets:
            if data_packet.packet_number == packet.requested_packet_number:
                self.send(data_packet)

    def process_control_packets(self):
        packet = self._recv(0)
        while (packet):
            self._process_one_control_packet(packet)
            packet = self._recv(0)

    def put_data(self, data: bytes) -> None:
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

            if self.data_packet_number_to_send % 2 == 1:
                self.send(packet)

            self.data_packet_number_to_send += 1
