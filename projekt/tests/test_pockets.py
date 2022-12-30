# some_file.py
import sys
# caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(1, 'projekt')
from packets import *


def test_to_binary():
    pocket = ConfirmationPacket(1, 2, 's', 2, "dawd")
    str = pocket.to_binary().encode('ascii')
    assert str == "412a2dawd"
