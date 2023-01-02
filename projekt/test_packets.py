import pytest
from packets import *


from projekt.packets_exceptions import *


def test_char_arr_to_bin():
    packet = Packet(1, 2)
    array = [1, 2, 'asd', 3]
    spreaded = packet._char_arr_to_bin(array)
    assert spreaded == [1, 2, b'asd', 3]


def test_get_stream_fmt_DataPacket():
    packet = ConfirmationPacket(1, 2, 1221, "haloo")
    format = packet.get_struct_fmt()
    assert format == "@iiii100s"


def test_get_stream_fmt_StreamControlPacket():
    packet = StreamControlPacket(1321, 2212, 'o', 12212)
    format = packet.get_struct_fmt()
    assert format == "@iiici"


def test_to_binary_ConfirmationPacket():
    packet = ConfirmationPacket(2, 3, 4, "halololo")
    output = packet.to_binary()

    fmt = packet.get_struct_fmt()
    unpacked = struct.unpack_from(fmt, output)
    assert unpacked[:4] == (4, 2, 3, 4)
    assert unpacked[4].decode('ascii').rstrip('\x00') == "halololo"


def test_to_binary_Packet():
    packet = StreamControlPacket(1321, 2212, 'o', 12212)
    output = packet.to_binary()

    fmt = packet.get_struct_fmt()
    unpacked = struct.unpack_from(fmt, output)
    assert unpacked == (2, 1321, 2212, b'o', 12212)


def test_too_long_data():
    with pytest.raises(TooLongDataError):
        packet = DataPacket(1, 2, 3, 101 * "a")
