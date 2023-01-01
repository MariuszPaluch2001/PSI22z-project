import sys
sys.path.insert(1, 'projekt')
from packets import *


def test_to_binary():
    pocket = ConfirmationPacket(1, 2, 's', 2, "dawd")
    output = pocket.to_binary()
    
    assert output == 0
    assert type(output) == type(bytes(0))

    assert output[:8] == b'00000100'
