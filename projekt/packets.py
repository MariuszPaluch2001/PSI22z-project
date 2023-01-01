from datetime import datetime


class Packet:

    def __init__(self, session_id, packet_number) -> None:
        self.packet_type = 0
        self.session_id = session_id
        self.packet_number = packet_number

    def to_binary(self):
        binary_str = ""

        fields_map = self.__dict__

        for key in fields_map.keys():
            val = fields_map[key]
            bin_val_str = ""

            if type(val) is str:
                for char in val:
                    bin_val_str += bin(ord(char))
            else:
                bin_val_str += bin(val)

            binary_str += str(bin_val_str)[1:]
        #temporary -> change that!
        return b''.join(ch.encode('ascii') for ch in binary_str)


class ControlPacket(Packet):

    def __init__(self, session_id, packet_number, control_type) -> None:
        super().__init__(session_id, packet_number)

        if (control_type not in ['o', 's', 'c']):
            raise TypeError
        self.control_type = control_type


class SessionControlPacket(ControlPacket):

    def __init__(self, session_id, packet_number, control_type) -> None:
        super().__init__(session_id, packet_number, control_type)
        self.packet_type = 1


class StreamControlPacket(ControlPacket):

    def __init__(self, session_id, packet_number, control_type, stream_id) -> None:
        super().__init__(session_id, packet_number, control_type)
        self.packet_type = 2
        self.stream_id = stream_id


class DataPacket(Packet):

    def __init__(self, session_id, stream_id, packet_number, data) -> None:
        super().__init__(session_id, packet_number)
        self.packet_type = 3
        self.stream_id = stream_id
        self.timestamp = datetime.now().isoformat()
        self.data = data


class ConfirmationPacket(StreamControlPacket):

    def __init__(self, session_id, packet_number, control_type, stream_id, data) -> None:
        super().__init__(session_id, packet_number, control_type, stream_id)
        self.packet_type = 4
        self.data = data


class RetransmissionRequestPacket(StreamControlPacket):

    def __init__(self, session_id, packet_number, control_type, stream_id) -> None:
        super().__init__(session_id, packet_number, control_type, stream_id)
        self.packet_type = 5
