import packets
import datetime

class Parser:
    def __init__(self) -> None:
        self.pointer = 0
        self.PACKET_TYPE_BIN_SIZE = 32
        self.SESSION_ID_BIN_SIZE = 32
        self.PACKET_NUMBER_BIN_SIZE = 32
        self.CONTROL_TYPE_BIN_SIZE = 8
        self.STREAM_ID_BIN_SIZE = 32
        self.TIMESTAMP_BIN_SIZE = 32

    def from_bin_to_int(self, bin_data) -> int:
        return int(bin_data, 2)

    def from_bin_to_chr(self, bin_data) -> str:
        return chr(self.from_bin_to_int(bin_data))

    def from_bin_to_date(self, bin_data) -> datetime.datetime:
        timestamp = self.from_bin_to_int(bin_data)
        return datetime.datetime.fromtimestamp(timestamp)

    def parse_packet(self, in_data) -> packets.Packet:
        self.pointer = 0

        packet_type = self.from_bin_to_int(in_data[:self.PACKET_TYPE_BIN_SIZE])
        self.pointer += self.PACKET_TYPE_BIN_SIZE

        if packet_type == 0:
            return packets.ErrorPacket()

        session_id = self.from_bin_to_int(in_data[self.pointer:self.pointer + self.SESSION_ID_BIN_SIZE])
        self.pointer += self.SESSION_ID_BIN_SIZE
        packet_number = self.from_bin_to_int(in_data[self.pointer:self.pointer + self.PACKET_NUMBER_BIN_SIZE])
        self.pointer += self.PACKET_NUMBER_BIN_SIZE

        if packet_type == 1:
            control_type = self.from_bin_to_chr(in_data[self.pointer:self.pointer + self.CONTROL_TYPE_BIN_SIZE])
            return packets.SessionControlPacket(session_id, packet_number, control_type)

        if packet_type == 2:
            control_type = self.from_bin_to_chr(in_data[self.pointer:self.pointer + self.CONTROL_TYPE_BIN_SIZE])
            self.pointer += self.CONTROL_TYPE_BIN_SIZE
            stream_id = self.from_bin_to_int(in_data[self.pointer:self.pointer + self.STREAM_ID_BIN_SIZE])
            return packets.StreamControlPacket(session_id, packet_number, control_type, stream_id)

        if packet_type == 3:
            stream_id = self.from_bin_to_int(in_data[self.pointer:self.pointer + self.STREAM_ID_BIN_SIZE])
            self.pointer += self.STREAM_ID_BIN_SIZE
            return packets.RetransmissionRequestPacket(session_id, packet_number, stream_id)

        if packet_type == 4:
            stream_id = self.from_bin_to_int(in_data[self.pointer:self.pointer + self.STREAM_ID_BIN_SIZE])
            self.pointer += self.STREAM_ID_BIN_SIZE
            data = in_data[self.pointer:]
            return packets.ConfirmationPacket(session_id, packet_number, stream_id, data)

        if packet_type == 5:
            stream_id = self.from_bin_to_int(in_data[self.pointer:self.pointer + self.STREAM_ID_BIN_SIZE])
            self.pointer += self.STREAM_ID_BIN_SIZE
            timestamp = self.from_bin_to_date(in_data[self.pointer:self.pointer + self.TIMESTAMP_BIN_SIZE])
            self.pointer += self.TIMESTAMP_BIN_SIZE
            data = in_data[self.pointer:]
            return packets.DataPacket(session_id, packet_number, stream_id, timestamp, data)
