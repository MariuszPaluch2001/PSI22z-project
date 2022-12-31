from session import *
from stream import (
    Stream
)

import pytest
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
    ret = s._receive_packet()
    assert isinstance(ret, SessionControlPacket)
    assert ret.session_id == 1
    assert ret.packet_number == 2
    assert ret.control_type == 'o'


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

def test_resend_packets():
    class DummySocket:
        def send(self, data): self.data = data
    
def test_send_packets_function():
    class DummySocket:
        def send(self, data): self.data = data
    ...