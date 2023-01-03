from session import *
from stream import (
    Stream
)
from datetime import datetime, timedelta
import pytest
import time
import threading

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
        Stream(1,1),
        Stream(1,1),
        Stream(1,1)
    ]
    streams[0].closed = True
    s.streams.extend(streams)
    assert s.stream_count() == 2


def test_get_active_streams():
    s = Session()
    active = s.get_active_streams()
    assert len(list(active)) == 0
    streams = [
        Stream(1,1),
        Stream(1,1),
        Stream(1,1)
    ]
    streams[0].closed = True
    s.streams.extend(streams)
    active = list(s.get_active_streams())
    assert len(active) == 2
    assert streams[1] in active
    assert streams[2] in active

def test_get_stream():
    s = Session()
    stream = Stream(1,2)
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
    packet = SessionControlPacket(1,last_current,'o')
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
    assert dummy.data[0] == unconfirmed[0][0].to_binary()
    assert dummy.data[1] == unconfirmed[1][0].to_binary()
    assert len(dummy.data) == 2
    assert unconfirmed[0][1] < datetime.now()
    assert unconfirmed[1][1] < datetime.now()

    
def test_send_packets_function():
    class DummySocket:
        def __init__(self): self.data = []
        def send(self, data): self.data.append(data)
    s = Session()
    dummy = DummySocket()
    s.socket = dummy
    s.is_open = True
    s.unconfirmed_packets = [
        [Packet(1,2), datetime.now() - timedelta(seconds=5)],
    ]
    stream1 = Stream(1,1)
    stream2 = Stream(1,2)
    s.streams.append(stream1)
    s.streams.append(stream2)
    stream1.message_buffer_out.append(Packet(1,3))

    s.send_packets()
    assert len(dummy.data) == 2
    assert dummy.data[0] == Packet(1,2).to_binary()
    assert dummy.data[1] == Packet(1,3).to_binary()
    
def test_close_stream():
    s = Session()
    s.streams = [
        Stream(1,1),
        Stream(1,2),
        Stream(1,3)
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
        Stream(1,1),
        Stream(1,2),
        Stream(1,3)
    ]
    assert s.get_max_stream_id() == 3

def test_create_client_session():
    cs = ClientSession()

def test_connection():
    check = False
    def server():
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                nonlocal check
                s.bind(('127.0.0.1',8030))
                data = s.recvfrom(128)
                check = (data[0] == SessionControlPacket(1,1,'o').to_binary())

    thread = threading.Thread(target=server)
    thread.start()
    s = ClientSession()
    s.connect("127.0.0.1", 8031, "127.0.0.1", 8030,1)
    assert s.is_open
    thread.join()
    s.close()
    assert check

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
    assert StreamControlPacket(1,1,'o',1).to_binary() == dummy.data[0]

def test_open_new_stream_after_max():
    s = ClientSession()
    s.streams = [ClientStream(1,i) for i in range(1,9)]
    with pytest.raises(MaximalStreamCountReached):
        s.open_new_stream()

def test_client_receive_data_packet():
    packet = DataPacket(1,1,1,b'abc')
    class DummySocket:
        def recvfrom(self, idk): return (packet.to_binary(), None)
    s = ClientSession()
    s.socket = DummySocket()
    s.is_open = True
    stream = ClientStream(1,1)
    s.streams.append(stream)
    s.receive_packet()
    ret = stream._get_packet()
    assert isinstance(ret, DataPacket)
    assert ret.to_binary() == packet.to_binary()

def test_client_receive_confirmation_packet():
    packet = ConfirmationPacket(1,1,1)
    class DummySocket:
        def recvfrom(self, idk): return (packet.to_binary(), None)
    s = ClientSession()
    s.socket = DummySocket()
    s.is_open = True
    s.unconfirmed_packets.append([Packet(1,1), datetime.now()])
    s.receive_packet()
    assert len(s.unconfirmed_packets) == 0

def test_client_receive_invalid_packet():
    packet = RetransmissionRequestPacket(1,1,1,1)
    class DummySocket:
        def recvfrom(self, idk): return (packet.to_binary(), None)
    s = ClientSession()
    s.socket = DummySocket()
    s.is_open = True
    with pytest.raises(InvalidPacket):
        s.receive_packet()

def test_client_receive_multiple_packets():
    packets = [
        ConfirmationPacket(1,1,1),
        ConfirmationPacket(1,2,0)
    ]

    class DummySocket:
        def recvfrom(self, idk): return (packets.pop().to_binary(), None)
    s = ClientSession()
    s.socket = DummySocket()
    s.is_open = True
    s.unconfirmed_packets.append([Packet(1,1), datetime.now()])
    s.unconfirmed_packets.append([Packet(1,2), datetime.now()])

    s.receive_packets(2)
    assert len(s.unconfirmed_packets) == 0

def test_close_client_session():
    class DummySocket:
        def send(self, data): self.data = data
        def close(self): self.closed = True
    s = ClientSession()
    s.streams = [ ClientStream(1,1)]
    dummy = DummySocket()
    s.socket = dummy
    s.is_open = True
    s.session_id = 1

    s.close()

    assert all(stream.is_closed() for stream in s.streams)
    assert dummy.closed is True
    assert dummy.data == SessionControlPacket(1,1,'c').to_binary()


def test_shutdown_client_session():
    class DummySocket:
        def send(self, data): self.data = data
        def close(self): self.closed = True
    s = ClientSession()
    s.streams = [ ClientStream(1,1)]
    dummy = DummySocket()
    s.socket = dummy
    s.is_open = True
    s.session_id = 1

    s.shutdown()

    assert all(stream.is_closed() for stream in s.streams)
    assert dummy.closed is True
    assert dummy.data == SessionControlPacket(1,1,'s').to_binary()

def test_create_server_session():
    ss = ServerSession()

def test_open_socket():
    SERVER_PORT = 9001
    CLIENT_PORT = 9000
    def dummy_client():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(("127.0.0.1", CLIENT_PORT))
            s.connect(("127.0.0.1", SERVER_PORT))
            s.send(SessionControlPacket(
                2,
                1,
                'o'
            ).to_binary())
    s = ServerSession()
    s.open_socket("127.0.0.1", SERVER_PORT)
    thread = threading.Thread(target=dummy_client)
    assert s.my_address == '127.0.0.1'
    assert s.my_port == SERVER_PORT
    thread.start()
    data = s.socket.recvfrom(128)
    packet_data = data[0]
    packet = Parser().parse_packet(packet_data)
    assert isinstance(packet, SessionControlPacket)
    assert packet.session_id == 2
    assert packet.packet_number == 1
    assert packet.control_type == 'o'
    thread.join()
    s.close()

def test_wait_for_connection():
    SERVER_PORT = 8021
    CLIENT_PORT = 8022
    confirm = None
    def dummy_client():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(("127.0.0.1", CLIENT_PORT))
            s.connect(("127.0.0.1", SERVER_PORT))
            s.send(SessionControlPacket(
                2,
                1,
                'o'
            ).to_binary())
            data = s.recvfrom(128)
            packet_data = data[0]
            nonlocal confirm
            confirm = Parser().parse_packet(packet_data)

    s = ServerSession()
    s.open_socket("127.0.0.1", SERVER_PORT)
    thread = threading.Thread(target=dummy_client)
    assert s.my_address == '127.0.0.1'
    assert s.my_port == SERVER_PORT
    thread.start()

    s.wait_for_connection()
    thread.join()
    assert s.is_open
    assert s.host_address == '127.0.0.1'
    assert s.host_port == CLIENT_PORT
    assert s.session_id == 2
    assert isinstance(confirm, ConfirmationPacket)
    assert confirm.session_id == 2
    assert confirm.packet_number == 1
    s.close()

def test_server_receive_session_closing_packet():
    packet = SessionControlPacket(1,1,'c')
    class DummySocket:
        def recvfrom(self, idk): return (packet.to_binary(), None)
        def send(self, data): pass
        def close(self): self.closed = True
    s = ServerSession()
    s.streams = [ ServerStream(1,1)]
    dummy = DummySocket()
    s.socket = dummy
    s.is_open = True
    s.session_id = 1
    s.receive_packet()
    assert s.streams[0].is_closed()
    assert s.is_open is False
    assert dummy.closed


def test_server_receive_session_shutting_packet():
    packet = SessionControlPacket(1,1,'s')
    class DummySocket:
        def recvfrom(self, idk): return (packet.to_binary(), None)
        def send(self, data): pass
        def close(self): self.closed = True
    s = ServerSession()
    s.streams = [ ServerStream(1,1)]
    dummy = DummySocket()
    s.socket = dummy
    s.is_open = True
    s.session_id = 1
    s.receive_packet()
    assert s.streams[0].is_closed()
    assert s.is_open is False
    assert dummy.closed

def test_server_receive_session_opening_packet():
    packet = SessionControlPacket(1,1,'o')
    class DummySocket:
        def recvfrom(self, idk): return (packet.to_binary(), None)
        def send(self, data): pass
    s = ServerSession()
    s.streams = [ ServerStream(1,1)]
    dummy = DummySocket()
    s.socket = dummy
    s.is_open = True
    s.session_id = 1
    s.receive_packet()
    assert s.streams[0].is_closed() is False
    assert s.is_open is True


def test_server_receive_stream_opening_packet():
    packet = StreamControlPacket(1,1,'o',1)
    class DummySocket:
        def recvfrom(self, idk): return (packet.to_binary(), None)
        def send(self, data): pass
    s = ServerSession()
    dummy = DummySocket()
    s.socket = dummy
    s.is_open = True
    s.session_id = 1
    s.receive_packet()
    assert len(s.streams) == 1
    assert s.streams[0].new == True


def test_server_receive_stream_opening_packet_max_streams():
    packet = StreamControlPacket(1,1,'o',1)
    class DummySocket:
        def recvfrom(self, idk): return (packet.to_binary(), None)
        def send(self, data): pass
    s = ServerSession()
    dummy = DummySocket()
    s.socket = dummy
    s.is_open = True
    s.session_id = 1
    s.streams = [ServerStream(1,i) for i in range(1,9)]
    s.receive_packet()
    assert len(s.streams) == 8

def test_server_receive_stream_control_packet():
    packet = StreamControlPacket(1,1,'c',1)
    class DummySocket:
        def recvfrom(self, idk): return (packet.to_binary(), None)
        def send(self, data): pass
    s = ServerSession()
    dummy = DummySocket()
    s.socket = dummy
    s.is_open = True
    s.session_id = 1
    s.streams = [ServerStream(1,i) for i in range(1,9)]
    assert len(list(s.get_active_streams())) == 8
    s.receive_packet()
    assert len(s.streams) == 8
    assert len(list(s.get_active_streams())) == 7
    assert s.streams[0].is_closed()

def test_server_receive_retransmission_packet():
    packet = RetransmissionRequestPacket(1,1,1,1)
    class DummySocket:
        def recvfrom(self, idk): return (packet.to_binary(), None)
        def send(self, data): pass
    s = ServerSession()
    dummy = DummySocket()
    s.socket = dummy
    s.is_open = True
    s.session_id = 1
    s.streams = [ServerStream(1,i) for i in range(1,9)]
    s.receive_packet() 
    ret = s.get_stream(1)._get_packet()
    assert ret.to_binary() == packet.to_binary()
    

def test_server_receive_invalid_packet():
    packet = DataPacket(1,2,3,b'abc')
    class DummySocket:
        def recvfrom(self, idk): return (packet.to_binary(), None)
        def send(self, data): pass
    s = ServerSession()
    dummy = DummySocket()
    s.socket = dummy
    s.is_open = True
    s.session_id = 1
    s.streams = [ServerStream(1,i) for i in range(1,9)]
    with pytest.raises(InvalidPacket):
        s.receive_packet() 


def test_server_receive_multiple_packets():
    packets = [StreamControlPacket(1,1,'o',1), StreamControlPacket(1,2,'o',2)]
    class DummySocket:
        def recvfrom(self, idk): return (packets.pop(0).to_binary(), None)
        def send(self, data): pass
    s = ServerSession()
    dummy = DummySocket()
    s.socket = dummy
    s.is_open = True
    s.session_id = 1
    s.receive_packets(2)
    assert len(s.streams) == 2
    assert s.streams[0].new is True
    assert s.streams[1].new is True
    assert s.streams[0].stream_id == 1
    assert s.streams[1].stream_id == 2


def test_get_new_streams():
    s = ServerSession()
    s.streams = [
        ServerStream(1,1),
        ServerStream(1,2),
        ServerStream(1,3),
    ]
    s.get_stream(1).new = False
    streams = s.get_new_streams()
    assert len(streams) == 2
    assert all(not stream.new for stream in streams)
    assert streams[0] is s.streams[1]
    assert streams[1] is s.streams[2]

def test_close_server_session():
    class DummySocket:
        def __init__(self): self.closed = False
        def close(self): self.closed = True
        def send(self): pass

    s = ServerSession()
    s.streams.append(ServerStream(1,1))
    s.socket = DummySocket()
    s.is_open = True
    s.close()
    assert s.is_open is False
    assert s.socket.closed is True
    assert s.streams[0].is_closed() is True

def test_shutdown_server_session():
    class DummySocket:
        def __init__(self): self.closed = False
        def close(self): self.closed = True
        def send(self): pass

    s = ServerSession()
    s.streams.append(ServerStream(1,1))
    s.socket = DummySocket()
    s.is_open = True
    s.shutdown()
    assert s.is_open is False
    assert s.socket.closed is True
    assert s.streams[0].is_closed() is True


def test_server_packet_confirmation():
    class DummySocket:
        def send(self,data): self.data = data

    s = ServerSession()
    s.socket = DummySocket()
    s.is_open = True
    s.session_id = 2
    s.confirm(2)
    packet = Parser().parse_packet(s.socket.data)
    assert isinstance(packet, ConfirmationPacket)
    assert packet.session_id == s.session_id
    assert packet.packet_number == 2
    assert packet.stream_id == 0