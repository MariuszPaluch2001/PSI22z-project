import argparse
import socket
import sys
from ctypes import c_long, c_short, c_char, Structure

BUFSIZE = 100
LOCALHOST = "127.0.0.1"

class data_struct(Structure):
    _fields_ = [('a', c_long), ('b', c_short), ('c', c_char*10)]


def main(port: int):
  print("Will listen on ", LOCALHOST, ":", port)
  try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
      s.bind((LOCALHOST, port))

      while True:
        data_address = s.recvfrom(BUFSIZE)
        data = data_address[0]
        recv_data = data_struct.from_buffer_copy(data)
        address = data_address[1]
        print(f'Message from Client: a = {recv_data.a} b = {recv_data.b} c = {recv_data.c.decode("utf-8")}')
        print("Client IP Address: {}".format(address))
        if not data:
          print("Error in datagram?")
          break
  except Exception as e:
    print(e)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('--port', type=int, required=True)
  args = parser.parse_args()
  main(args.port)
