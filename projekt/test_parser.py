# STRumyk, Dominik Łopatecki, 02.01.2023

from Parser import Parser
import packets
import time
from datetime import datetime


def test_reading_ErrorPacket():
    parser_test = Parser()
    bin_data = b'\x00\x00\x00\x00\x0b\x00\x00\x00\x14\x00\x00\x00'

    new_packet = parser_test.parse_packet(bin_data)

    assert isinstance(new_packet, packets.ErrorPacket)
    assert new_packet.packet_type == 0
    assert new_packet.session_id == 11
    assert new_packet.packet_number == 20


def test_reading_ErrorPacketUsingPacketObject():
    parser_test = Parser()
    packet_test = packets.ErrorPacket(2, 51)

    new_packet = parser_test.parse_packet(packet_test.to_binary())

    assert isinstance(new_packet, packets.ErrorPacket)
    assert new_packet.packet_type == 0
    assert new_packet.session_id == 2
    assert new_packet.packet_number == 51


def test_reading_SessionControlPacket():
    parser_test = Parser()
    bin_data = b'\x01\x00\x00\x00\x29\x05\x00\x00\xd5\x00\x00\x00\x6F'

    new_packet = parser_test.parse_packet(bin_data)

    assert isinstance(new_packet, packets.SessionControlPacket)
    assert new_packet.packet_type == 1
    assert new_packet.session_id == 1321
    assert new_packet.packet_number == 213
    assert new_packet.control_type == 'o'


def test_reading_SessionControlPacketUsingPacketObject():
    parser_test = Parser()
    packet_test = packets.SessionControlPacket(21, 3, 'c')

    new_packet = parser_test.parse_packet(packet_test.to_binary())

    assert isinstance(new_packet, packets.SessionControlPacket)
    assert new_packet.packet_type == 1
    assert new_packet.session_id == 21
    assert new_packet.packet_number == 3
    assert new_packet.control_type == 'c'


def test_reading_StreamControlPacket():
    parser_test = Parser()
    bin_data = b'\x02\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00o\x00\x00\x00\x05\x00\x00\x00'
    new_packet = parser_test.parse_packet(bin_data)

    isinstance(new_packet, packets.StreamControlPacket)
    assert new_packet.packet_type == 2
    assert new_packet.session_id == 1
    assert new_packet.packet_number == 3
    assert new_packet.control_type == 'o'
    assert new_packet.stream_id == 5


def test_reading_StreamControlPacketUsingPacketObject():
    parser_test = Parser()
    packet_test = packets.StreamControlPacket(2, 1, 's', 7)

    new_packet = parser_test.parse_packet(packet_test.to_binary())

    isinstance(new_packet, packets.StreamControlPacket)
    assert new_packet.packet_type == 2
    assert new_packet.session_id == 2
    assert new_packet.packet_number == 1
    assert new_packet.control_type == 's'
    assert new_packet.stream_id == 7


def test_reading_RetransmissionRequestPacket():
    parser_test = Parser()
    bin_data = b'\x03\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00\x07\x00\x00\x00\x19\x00\x00\x00'
    new_packet = parser_test.parse_packet(bin_data)

    isinstance(new_packet, packets.RetransmissionRequestPacket)
    assert new_packet.packet_type == 3
    assert new_packet.session_id == 1
    assert new_packet.packet_number == 3
    assert new_packet.stream_id == 7
    assert new_packet.requested_packet_number == 25


def test_reading_RetransmissionRequestPacketUsingPacketObject():
    parser_test = Parser()
    packet_test = packets.RetransmissionRequestPacket(90, 32, 31, 1)

    new_packet = parser_test.parse_packet(packet_test.to_binary())

    isinstance(new_packet, packets.RetransmissionRequestPacket)
    assert new_packet.packet_type == 3
    assert new_packet.session_id == 90
    assert new_packet.packet_number == 32
    assert new_packet.stream_id == 31
    assert new_packet.requested_packet_number == 1


def test_reading_ConfirmationPacketPacket():
    parser_test = Parser()
    bin_data = b'\x04\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\xc5\x04\x00\x00'

    new_packet = parser_test.parse_packet(bin_data)

    isinstance(new_packet, packets.ConfirmationPacket)
    assert new_packet.packet_type == 4
    assert new_packet.session_id == 1
    assert new_packet.packet_number == 2
    assert new_packet.stream_id == 1221


def test_reading_ConfirmationPacketUsingPacketObject():
    parser_test = Parser()
    packet_test = packets.ConfirmationPacket(1, 2, 3)

    new_packet = parser_test.parse_packet(packet_test.to_binary())

    isinstance(new_packet, packets.ConfirmationPacket)
    assert new_packet.packet_type == 4
    assert new_packet.session_id == 1
    assert new_packet.packet_number == 2
    assert new_packet.stream_id == 3


def test_reading_DataPacket():
    parser_test = Parser()
    bin_data = b'\x05\x00\x00\x00\x0b\x00\x00\x00\x0b\x00\x00\x00\x0b\x00\x00\x00\x97\x1b\xb3\x63\x74\x65\x73\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    new_packet = parser_test.parse_packet(bin_data)

    isinstance(new_packet, packets.DataPacket)
    assert new_packet.packet_type == 5
    assert new_packet.session_id == 11
    assert new_packet.packet_number == 11
    assert new_packet.stream_id == 11
    assert new_packet.timestamp == 1672682391
    assert new_packet.data[:4] == b'test'


def test_reading_DataPacketUsingPacketObject():
    parser_test = Parser()
    timestamp = int(time.mktime(datetime.now().timetuple()))
    packet_test = packets.DataPacket(8, 9, 10, b'hello', timestamp)

    new_packet = parser_test.parse_packet(packet_test.to_binary())

    isinstance(new_packet, packets.DataPacket)
    assert new_packet.packet_type == 5
    assert new_packet.session_id == 8
    assert new_packet.packet_number == 9
    assert new_packet.stream_id == 10
    assert new_packet.timestamp == timestamp
    assert new_packet.data[:5] == b'hello'


def test_reading_non_existing_packet():
    parser_test = Parser()
    bin_data = b'\x07\x00\x00\x00\x0b\x00\x00\x00\x14\x00\x00\x00'
    is_non_existing = False

    new_packet = parser_test.parse_packet(bin_data)

    assert new_packet is None
