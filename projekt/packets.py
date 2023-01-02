from datetime import datetime
import struct
import time


class Packet:

    def __init__(self, session_id, packet_number) -> None:
        self.packet_type = 0
        self.session_id = session_id
        self.packet_number = packet_number

    def get_struct_fmt(self) -> str:
        fields_map = self.__dict__
        format = "@"

        for key in fields_map.keys():
            if key == "control_type":
                format += "c"
            elif key == "data":
                format += "100s"
            else:
                format += "i"

        return format

    @staticmethod
    def _char_arr_to_bin(array) -> list:
        output = []
        for element in array:
            if type(element) is str:
                output.append(bytes(element, encoding='ascii'))
            else:
                output.append(element)
        return output

    def to_binary(self) -> bytes:
        struct_format = self.get_struct_fmt()

        fields_map = self.__dict__
        struct_array = self._char_arr_to_bin(fields_map.values())

        return struct.pack(struct_format, *struct_array)


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


class RetransmissionRequestPacket(Packet):

    def __init__(self, session_id, packet_number, stream_id, requested_packet_number) -> None:
        super().__init__(session_id, packet_number)
        self.packet_type = 3
        self.stream_id = stream_id
        self.requested_packet_number = requested_packet_number


class ConfirmationPacket(Packet):

    def __init__(self, session_id, packet_number, stream_id, data) -> None:
        super().__init__(session_id, packet_number)
        self.packet_type = 4
        self.stream_id = stream_id
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
