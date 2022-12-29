class Packet:
    
    def __init__(self, session_id, packet_number) -> None:
        self.session_id = session_id
        self.packet_number = packet_number

    def to_binary():
        raise NotImplementedError

class SessionOpenPacket(Packet):
    
    def __init__(self, session_id, packet_number) -> None:
        super().__init__(session_id, packet_number)

class SessionClosePacket(Packet):
    
    def __init__(self, session_id, packet_number) -> None:
        super().__init__(session_id, packet_number)

class SessionShutdownPacket(Packet):
    
    def __init__(self, session_id, packet_number) -> None:
        super().__init__(session_id, packet_number)

class StreamOpenPacket(Packet):
    
    def __init__(self, session_id, packet_number) -> None:
        super().__init__(session_id, packet_number)

class StreamClosePacket(Packet):
    
    def __init__(self, session_id, packet_number) -> None:
        super().__init__(session_id, packet_number)

class DataPacket(Packet):
    
    def __init__(self, session_id, packet_number) -> None:
        super().__init__(session_id, packet_number)

class ConfirmationPacket(Packet):
    
    def __init__(self, session_id, packet_number) -> None:
        super().__init__(session_id, packet_number)
	
class RetransmissionRequestPacket(Packet):
    
    def __init__(self, session_id, packet_number) -> None:
        super().__init__(session_id, packet_number)
