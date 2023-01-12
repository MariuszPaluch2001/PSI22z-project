from packets import *

class Logger:
    def __init__(self) -> None:
        pass

    def write_packet_info(self, caller: str, packet: Packet):
        if isinstance(packet, RetransmissionRequestPacket):
            print(f'{caller}: stream_id={packet.stream_id} session_id={packet.session_id} '
                  f'number={packet.packet_number} retr={packet.requested_packet_number} type=RetransmissionRequestPacket')
        else:
            print(f'{caller}: stream_id={packet.stream_id} session_id={packet.session_id} '
                  f'number={packet.packet_number} type=DataPacket')

    def write_log(self, caller: str, message: str):
        print(f"!!!!!{caller}: {message}")