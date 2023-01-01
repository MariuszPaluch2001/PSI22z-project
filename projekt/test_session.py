from session import *
from stream import (
    Stream
)
from datetime import datetime
import pytest
import time

def test_create_session():
    s = Session()
    assert len(s.streams) == 0
    assert s.socket is None
    assert s.current_packet_number == 1
    assert len(s.unconfirmed_packets) == 0
    assert s.is_open is False

def test_stream_count():
    s = Session()
    assert s.stream_count() == 0
    streams = [
        Stream(1),
        Stream(1),
        Stream(1)
    ]
    streams[0].closed = True
    s.streams.extend(streams)
    assert s.stream_count() == 2


def test_get_active_streams():
    s = Session()
    active = s.get_active_streams()
    assert len(list(active)) == 0
    streams = [
        Stream(1),
        Stream(1),
        Stream(1)
    ]
    streams[0].closed = True
    s.streams.extend(streams)
    active = list(s.get_active_streams())
    assert len(active) == 2
    assert streams[1] in active
    assert streams[2] in active

def test_get_stream():
    s = Session()
    stream = Stream(2)
    s.streams.append(stream)
    ret = s.get_stream(2)
    assert ret is stream

def test_get_nonexisting_stream():
    s = Session()
    with pytest.raises(StreamNotFound):
        s.get_stream(2)
    
def test_monkeypatched_packet_sending():
    class DummySocket:
        def send(self, data): self.data = data
    
    s = Session()
    dummy = DummySocket()
    s.socket = dummy
    s.is_open = True
    packet = SessionControlPacket(1,2,'o')
    s._send_packet(packet)
    assert dummy.data == packet.to_binary()


def test_monkeypatched_packet_sending_without_opening():
    class DummySocket:
        def __init__(self): self.touched = False
        def send(self, data): self.touched = True
    s = Session()
    dummy = DummySocket()
    s.socket = dummy
    packet = SessionControlPacket(1,2,'o')
    s._send_packet(packet)
    assert dummy.touched is False

def test_monkeypatched_control_packet_sending():
    class DummySocket:
        def send(self, data): self.data = data
    
    s = Session()
    dummy = DummySocket()
    s.socket = dummy
    s.is_open = True
    last_current = s.current_packet_number
    packet = SessionControlPacket(1,2,'o')
    s._send_control_packet(packet)
    assert dummy.data == packet.to_binary()
    assert s.current_packet_number == last_current + 1
    assert len(s.unconfirmed_packets) == 1
    ret = s.unconfirmed_packets[0][0]
    assert ret is packet

def test_monkeypatched_control_packet_sending_without_opening():
    class DummySocket:
        def __init__(self): self.touched = False
        def send(self, data): self.touched = True
    s = Session()
    dummy = DummySocket()
    s.socket = dummy
    last_current = s.current_packet_number
    packet = SessionControlPacket(1,2,'o')
    s._send_control_packet(packet)
    assert dummy.touched is False
    assert s.current_packet_number == last_current
    assert len(s.unconfirmed_packets) == 0

def test_monkeypatched_packet_receiving():
    packet = SessionControlPacket(1,2,'o')
    class DummySocket:
        def recvfrom(self, _): return (packet.to_binary(),)
    s = Session()
    dummy = DummySocket()
    s.socket = dummy
    s.is_open = True
    #ret = s._receive_packet()
    #assert isinstance(ret, SessionControlPacket)
    #assert ret.session_id == 1
    #assert ret.packet_number == 2
    #assert ret.control_type == 'o'


def test_monkeypatched_packet_receiving_without_opening():
    packet = SessionControlPacket(1,2,'o')
    class DummySocket:
        def __init__(self): self.touched = False
        def recvfrom(self, _): self.touched = True
    s = Session()
    dummy = DummySocket()
    s.socket = dummy
    ret = s._receive_packet()
    assert ret is None
    assert dummy.touched is False

def test_monkeypatched_resend_packets():
    class DummySocket:
        def __init__(self): self.data = []
        def send(self, data): self.data.append(data)
    s = Session()
    dummy = DummySocket()
    s.socket = dummy
    s.is_open = True
    unconfirmed = [
        [Packet(1,2), datetime.now()],
        [Packet(1,3), datetime.now()]
    ]
    time.sleep(5)
    unconfirmed.append([Packet(1,4), datetime.now()])
    s.unconfirmed_packets = unconfirmed

    s.resend_packets()
    parser = Parser()
    assert len(dummy.data) == 2
    #assert parser.parse_packet(dummy.data[0]).packet_number == 2
    #assert parser.parse_packet(dummy.data[0]).session_id == 1
    assert unconfirmed[0][1] < datetime.now()
    #assert parser.parse_packet(dummy.data[0]).packet_number == 3
    #assert parser.parse_packet(dummy.data[0]).session_id == 1
    assert unconfirmed[1][1] < datetime.now()

    
def test_send_packets_function():
    ...

def test_close_stream():
    s = Session()
    s.streams = [
        Stream(1),
        Stream(2),
        Stream(3)
    ]
    s.close_stream(2)
    assert s.streams[1].is_closed() is True

def test_confirm_packet():
    s = Session()
    s.unconfirmed_packets = [
        [Packet(1,2), datetime.now()],
        [Packet(1,3), datetime.now()]
    ]
    s.confirm_packet(3)
    assert len(s.unconfirmed_packets) == 1
    assert s.unconfirmed_packets[0][0].packet_number == 2

def test_double_confirm_packet():
    s = Session()
    s.unconfirmed_packets = [
        [Packet(1,2), datetime.now()],
        [Packet(1,3), datetime.now()]
    ]
    s.confirm_packet(3)
    assert len(s.unconfirmed_packets) == 1
    assert s.unconfirmed_packets[0][0].packet_number == 2
    s.confirm_packet(3)
    assert len(s.unconfirmed_packets) == 1
    assert s.unconfirmed_packets[0][0].packet_number == 2

def test_get_max_stream_id():
    s = Session()
    s.streams = [
        Stream(1),
        Stream(2),
        Stream(3)
    ]
    assert s.get_max_stream_id() == 3

def test_create_client_session():
    cs = ClientSession()

def test_connection():
    ...

def test_open_new_stream():
    class DummySocket:
        def __init__(self): self.data = []
        def send(self, data): self.data.append(data)
    s = ClientSession()
    dummy = DummySocket()
    s.socket = dummy
    s.is_open = True
    s.session_id = 1
    ret = s.open_new_stream()
    assert isinstance(ret, ClientStream)
    assert len(dummy.data) == 1
    #packet = Parser().parse_packet(dummy.data[0])
    #assert isinstance(packet, StreamControlPacket)
    #assert packet.session_id == 1
    #assert packet.packet_number == 1
    #assert packet.control_type == 'o'
    #assert packet.stream_id == 1

def test_open_new_stream_after_max():
    s = ClientSession()
    s.streams = [ClientStream(i) for i in range(1,9)]
    with pytest.raises(MaximalStreamCountReached):
        s.open_new_stream()

def test_client_receive_packets():
    ...

def test_close_client_session():
    ...

def test_shutdown_client_session():
    ...

def test_create_server_session():
    ss = ServerSession()

def test_wait_for_connection():
    ...

def test_server_receive_packets():
    ...

def test_get_new_streams():
    ...

def test_close_server_session():
    ...

def test_shutdown_server_session():
    ...