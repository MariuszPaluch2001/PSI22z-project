from threading import Thread
import time

from stream import Stream, ClientStream, ServerStream
from packets import DataPacket, RetransmissionRequestPacket
import pytest

def test_put_packet_out_simple():
    test_stream = Stream(1, 1)
    data_packet = DataPacket(1, 1, 1, b'')
    test_stream.send(data_packet)
    assert len(test_stream.message_buffer_out) == 1
    assert test_stream.message_buffer_out[0].packet_number == 1


def test_get_packet_in_simple():
    test_stream = Stream(1, 1)
    data_packet = DataPacket(1, 1, 1, b'')
    test_stream.message_buffer_in.put((data_packet.packet_number, data_packet))
    assert test_stream._recv() == data_packet

def test_upload_packet_not_impl_err():
    s = Stream(1,1)
    with pytest.raises(NotImplementedError):
        s._upload_packet(DataPacket(1,1,1,bytearray(b'')))

def test_put_packet_in_simple():
    test_stream = ClientStream(1, 1)
    data_packet = DataPacket(1, 1, 1, b'')
    test_stream.upload_packet(data_packet)
    assert test_stream.message_buffer_in.get()[1] == data_packet


def test_get_packet_out_simple():
    test_stream = Stream(1, 1)
    data_packet = DataPacket(1, 1, 1, b'')
    test_stream.message_buffer_out.append((data_packet))
    assert test_stream.get_packet() == data_packet


def test_mutex_in_sync():
    test_stream = ClientStream(1, 1)
    data_packet_1 = DataPacket(1, 1, 1, b'')

    def writer():
        test_stream.upload_packet(data_packet_1)

    thread = Thread(target=writer)
    thread.start()
    assert test_stream._recv(1) == data_packet_1


def test_mutex_out_sync():
    test_stream = Stream(1, 1)
    data_packet_1 = DataPacket(1, 1, 1, b'')

    def writer():
        test_stream.send(data_packet_1)

    thread = Thread(target=writer)
    thread.start()
    assert test_stream.get_packet() == data_packet_1

def test_get_message_return_none():
    test_stream = ClientStream(1,1)
    assert test_stream.get_message(1) is None

def test_simple_get_messages():
    test_stream = ClientStream(1, 1)

    data_packet_1 = DataPacket(1, 1, 1, b'')
    data_packet_2 = DataPacket(1, 2, 1, b'')
    data_packet_3 = DataPacket(1, 3, 1, b'')

    test_stream.message_buffer_in.put(
        (data_packet_1.packet_number, data_packet_1))
    test_stream.message_buffer_in.put(
        (data_packet_2.packet_number, data_packet_2))
    test_stream.message_buffer_in.put(
        (data_packet_3.packet_number, data_packet_3))
    assert test_stream.get_message(10).packet_number == 1
    assert test_stream.get_message(10).packet_number == 2
    assert test_stream.get_message(10).packet_number == 3


def test_missing_get_messages():
    test_stream = ClientStream(1, 1)

    data_packet_1 = DataPacket(1, 1, 1, b'')
    data_packet_2 = DataPacket(1, 2, 1, b'')
    data_packet_3 = DataPacket(1, 3, 1, b'')
    data_packet_4 = DataPacket(1, 4, 1, b'')

    test_stream.message_buffer_in.put(
        (data_packet_2.packet_number, data_packet_2))
    test_stream.message_buffer_in.put(
        (data_packet_3.packet_number, data_packet_3))
    test_stream.message_buffer_in.put(
        (data_packet_4.packet_number, data_packet_4))

    def session_simulator():
        time.sleep(1)
        test_stream.post(data_packet_1)

    thread = Thread(target=session_simulator)
    thread.start()

    assert test_stream.get_message(10).packet_number == 1
    assert test_stream.get_message(10).packet_number == 2
    assert test_stream.get_message(10).packet_number == 3
    assert test_stream.get_message(10).packet_number == 4


def test_missing_without_sleep_get_messages():
    test_stream = ClientStream(1, 1)

    data_packet_1 = DataPacket(1, 1, 1, b'')
    data_packet_2 = DataPacket(1, 2, 1, b'')
    data_packet_3 = DataPacket(1, 3, 1, b'')
    data_packet_4 = DataPacket(1, 4, 1, b'')

    test_stream.message_buffer_in.put(
        (data_packet_2.packet_number, data_packet_2))
    test_stream.message_buffer_in.put(
        (data_packet_3.packet_number, data_packet_3))
    test_stream.message_buffer_in.put(
        (data_packet_4.packet_number, data_packet_4))

    def session_simulator():
        time.sleep(1)
        test_stream.post(data_packet_1)

    thread = Thread(target=session_simulator)
    thread.start()

    assert test_stream.get_message(10).packet_number == 1
    assert test_stream.get_message(10).packet_number == 2
    assert test_stream.get_message(10).packet_number == 3
    assert test_stream.get_message(10).packet_number == 4


def test_empty_get_all_messages():

    test_stream = ClientStream(1, 1)

    assert test_stream.get_all_messages() == []


def test_simple_get_all_messages():
    test_stream = ClientStream(1, 1)

    data_packets = [DataPacket(1, 1, 1, b''),
                    DataPacket(1, 2, 1, b''),
                    DataPacket(1, 3, 1, b'')]

    for packet in data_packets:
        test_stream.message_buffer_in.put((packet.packet_number, packet))

    assert test_stream.get_all_messages() == data_packets


def test_mixed_get_all_messages():
    test_stream = ClientStream(1, 1)

    data_packets = [DataPacket(1, 1, 1, b''),
                    DataPacket(1, 3, 1, b''),
                    DataPacket(1, 4, 1, b'')]

    for packet in data_packets:
        test_stream.message_buffer_in.put((packet.packet_number, packet))

    messages = test_stream.get_all_messages()
    assert len(messages) == 1
    assert messages[0] == data_packets[0]

    messages = test_stream.get_all_messages()
    assert len(messages) == 0

    missing_packet = DataPacket(1, 2, 1, b'')
    test_stream.message_buffer_in.put(
        (missing_packet.packet_number, missing_packet))

    messages = test_stream.get_all_messages()
    assert len(messages) == 3
    assert messages[0] == missing_packet
    assert messages[1] == data_packets[1]
    assert messages[2] == data_packets[2]


def test_request_retransmission():
    test_stream = ClientStream(1, 1)
    test_stream._request_retransmission(1)

    assert type(
        test_stream.message_buffer_out[0]) is RetransmissionRequestPacket
    assert test_stream.message_buffer_out[0].requested_packet_number == 1


def test_process_control_packets_RetransmissionRequestPacket():
    test_stream = ServerStream(1, 1)
    data_packet_1 = DataPacket(1, 1, 1, bytearray(b""))
    data_packet_2 = DataPacket(1, 1, 1, bytearray(b""))
    test_stream.data_packets.append(data_packet_1)
    test_stream.data_packets.append(data_packet_2)
    test_stream.upload_packet(RetransmissionRequestPacket(1, 1, 1, 1))
    test_stream.upload_packet(RetransmissionRequestPacket(1, 2, 1, 2))
    test_stream.process_control_packets()
    test_stream.message_buffer_out[0] == data_packet_1
    test_stream.message_buffer_out[1] == data_packet_2


def test_put_data_server_stream_empty():
    test_stream = ServerStream(1, 1)
    test_stream.put_data(b'')
    assert len(test_stream.data_packets) == 0


def test_put_data_server_stream_without_padding():
    test_stream = ServerStream(1, 1)
    test_stream.put_data(b'0'*100*4)
    assert len(test_stream.data_packets) == 4
    assert [elem.data for elem in test_stream.data_packets] == [
        bytearray(b'0'*100) for _ in range(4)]


def test_put_data_server_stream_with_padding():
    test_stream = ServerStream(1, 1)
    test_stream.put_data(b'0'*150)
    assert len(test_stream.data_packets) == 2
    assert test_stream.data_packets[0].data == bytearray(b'0'*100)
    assert test_stream.data_packets[1].data == bytearray(b'0'*50)


def test_retransmission():
    serv = ServerStream(1, 1)
    client = ClientStream(1, 1)
    data_packets = [DataPacket(1, i, 1, bytearray()) for i in range(8)]
    serv.data_packets = data_packets
    for i, packet in enumerate(data_packets):
        if i % 2:
            ...
