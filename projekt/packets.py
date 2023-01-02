from datetime import datetime
import time


def str_to_bin(val: str):
    output = ""
    for char in val:
        output += "{:08b}".format(ord(char))
    return output


def str_to_bin_stream(string):
    n = 8
    chunks = [string[i:i+n] for i in range(0, len(string), n)]
    output = ""
    for chunk in chunks:
        output += chr(int(chunk, base=2))
    return bytes(output, encoding='ascii')


class Packet:

    def __init__(self, session_id, packet_number) -> None:
        self.packet_type = 0
        self.session_id = session_id
        self.packet_number = packet_number

    def to_binary(self) -> bytes:
        binary_str = ""
        fields_map = self.__dict__

        for key in fields_map.keys():
            val = fields_map[key]

            if key == "packet_type":
                binary_str += "{:08b}".format(val)
            elif type(val) is str:
                binary_str += str_to_bin(val)
            else:
                binary_str += "{:032b}".format(val)

        return str_to_bin_stream(binary_str)


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


class RetransmissionRequestPacket(StreamControlPacket):

    def __init__(self, session_id, packet_number, control_type, stream_id) -> None:
        super().__init__(session_id, packet_number, control_type, stream_id)
        self.packet_type = 3


class ConfirmationPacket(StreamControlPacket):

    def __init__(self, session_id, packet_number, control_type, stream_id, data) -> None:
        super().__init__(session_id, packet_number, control_type, stream_id)
        self.packet_type = 4
        self.data = data


class DataPacket(Packet):

    def __init__(self, session_id, stream_id, packet_number, data) -> None:
        super().__init__(session_id, packet_number)
        self.packet_type = 5
        self.stream_id = stream_id
        self.timestamp = int(time.mktime(datetime.now().timetuple()))
        self.data = data


class ErrorPacket(Packet):

    def __init__(self, session_id, packet_number) -> None:
        super().__init__(session_id, packet_number)
