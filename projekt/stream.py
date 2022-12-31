from packets import *

class Stream:
    def __init__(self,stream_id,logger) -> None:
        self.stream_id = stream_id

        self.logger = logger
        #Kolejki - kolejki priorytetowe ?
        self.message_buffer_in = []
        self.message_buffer_out = []
        self.last_message_index = 0

    def get_message(self):
        for packet in self.message_buffer_in:
            if type(packet) is DataPacket:
                if packet.packet_number == self.last_message_index + 1:
                    self.last_message_index += 1
                    self.message_buffer_in.remove(packet)
                    return packet
                elif packet.packet_number > self.last_message_index + 1:
                    self.message_buffer_out.append(
                        RetransmissionRequestPacket(None, # skąd to wziąść?
                                                    self.last_message_index + 1, 
                                                    None, # skąd to wziąść?
                                                    self.stream_id)
                    )

    def get_all_messages(self):
        packet_number_current = self.last_message_index
        packets = []
        for packet in self.message_buffer_in:
            if type(packet) is DataPacket:
                if packet.packet_number == packet_number_current:
                    packet_number_current += 1
                    self.message_buffer_in.remove(packet)
                    packets.append(packet)
                elif packet.packet_number > packet_number_current:
                    self.message_buffer_out.append(
                        RetransmissionRequestPacket(None, # skąd to wziąść?
                                                    self.last_message_index + 1, 
                                                    None, # skąd to wziąść?
                                                    self.stream_id)
                    )
                    return packets
        
        return packets

    def put_message(self, binary_stream : bytes):
        ...
    
    def process_control_packets(self):
        raise NotImplementedError()

class ClientStream(Stream):
    def __init__(self, stream_id, logger) -> None:
        super().__init__(stream_id, logger)

    def process_control_packets(self):
        ...

class ServerStream(Stream):
    def __init__(self, stream_id, logger) -> None:
        super().__init__(stream_id, logger)

    def process_control_packets(self):
        ...