from threading import Thread
import time

from stream import Stream, ClientStream, ServerStream
from packets import DataPacket

def test_put_packet_out():
    test_stream = Stream(1, 1)
    data_packet_1 = DataPacket(1,1,1, b'')
    test_stream.put_packet()


def test_simple_get_messages():
    test_stream = ClientStream(1, 1)
    
    data_packet_1 = DataPacket(1,1,1, b'')
    data_packet_2 = DataPacket(1,1,2, b'')
    data_packet_3 = DataPacket(1,1,3, b'')
    
    test_stream.message_buffer_in.put((data_packet_1.packet_number, data_packet_1))
    test_stream.message_buffer_in.put((data_packet_2.packet_number, data_packet_2))
    test_stream.message_buffer_in.put((data_packet_3.packet_number, data_packet_3))
    assert test_stream.get_message(10).packet_number == 1
    assert test_stream.get_message(10).packet_number == 2
    assert test_stream.get_message(10).packet_number == 3

def test_missing_get_messages():
    test_stream = ClientStream(1, 1)
    
    data_packet_1 = DataPacket(1,1,1, b'')
    data_packet_2 = DataPacket(1,1,2, b'')
    data_packet_3 = DataPacket(1,1,3, b'')
    data_packet_4 = DataPacket(1,1,4, b'')
    
    test_stream.message_buffer_in.put((data_packet_2.packet_number, data_packet_2))
    test_stream.message_buffer_in.put((data_packet_3.packet_number, data_packet_3))
    test_stream.message_buffer_in.put((data_packet_4.packet_number, data_packet_4))
    
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
    
    data_packet_1 = DataPacket(1,1,1, b'')
    data_packet_2 = DataPacket(1,1,2, b'')
    data_packet_3 = DataPacket(1,1,3, b'')
    data_packet_4 = DataPacket(1,1,4, b'')
    
    test_stream.message_buffer_in.put((data_packet_2.packet_number, data_packet_2))
    test_stream.message_buffer_in.put((data_packet_3.packet_number, data_packet_3))
    test_stream.message_buffer_in.put((data_packet_4.packet_number, data_packet_4))
    
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
    
    data_packets = [DataPacket(1,1,1, b''),
                    DataPacket(1,1,2, b''), 
                    DataPacket(1,1,3, b'')]
    
    for packet in data_packets:
        test_stream.message_buffer_in.put((packet.packet_number, packet))

    assert test_stream.get_all_messages() == data_packets


def test_mixed_get_all_messages():
    test_stream = ClientStream(1, 1)
    
    data_packets = [DataPacket(1,1,1, b''), 
                    DataPacket(1,1,3, b''), 
                    DataPacket(1,1,4, b'')]
    
    for packet in data_packets:
        test_stream.message_buffer_in.put((packet.packet_number, packet))

    messages = test_stream.get_all_messages()
    assert len(messages) == 1
    assert messages[0] == data_packets[0]
    
    messages = test_stream.get_all_messages()
    assert len(messages) == 0

    missing_packet = DataPacket(1,1,2, b'')
    test_stream.message_buffer_in.put((missing_packet.packet_number, missing_packet))

    messages = test_stream.get_all_messages()
    assert len(messages) == 3
    assert messages[0] == missing_packet
    assert messages[1] == data_packets[1]
    assert messages[2] == data_packets[2]


