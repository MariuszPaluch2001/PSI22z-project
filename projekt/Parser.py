import struct
import packets

class Parser:
    def __init__(self) -> None:
        self.formats = {0: "@hii",
                        1: "@hiic",
                        2: "@hiici",
                        3: "@hiiii",
                        4: "@hiii",
                        5: "@hiiii100s"}

    def parse_packet(self, input_data) -> packets.Packet:
        packet_type = input_data[0]

        if packet_type not in self.formats.keys():
            raise Exception("Incorrect type of packet")

        format = self.formats[packet_type]
        packet_fields = struct.unpack_from(format, input_data)

        if packet_type == 0:
            return packets.ErrorPacket(*packet_fields[1:])

        if packet_type == 1:
            control_type = packet_fields[3].decode('ascii')
            return packets.SessionControlPacket(*packet_fields[1:3], control_type)

        if packet_type == 2:
            control_type = packet_fields[3].decode('ascii')
            return packets.StreamControlPacket(*packet_fields[1:3], control_type, packet_fields[4])

        if packet_type == 3:
            return packets.RetransmissionRequestPacket(*packet_fields[1:])

        if packet_type == 4:
            return packets.ConfirmationPacket(*packet_fields[1:])

        if packet_type == 5:
            data = bytes(packet_fields[5].decode('ascii').rstrip('\x00'), encoding='ascii')
            return packets.DataPacket(*packet_fields[1:4], data, packet_fields[4])
