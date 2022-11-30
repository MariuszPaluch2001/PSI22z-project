import argparse
import socket

SIZE = 100
SEND_COUNT = 3


def main(server_address: str, port: int):
  try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
      for i in range(SEND_COUNT):
        stream_data = b"kocham studiowac!!"
        s.sendto(stream_data, (server_address, port))

        data = s.recv(SIZE)
        print('Received data=', repr(data), " size= ", SIZE)
  except Exception as e:
    print(e)

  print('Client finished.')

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('--server_address', type=str, required=True)
  parser.add_argument('--port', type=int, required=True)
  args = parser.parse_args()
  main(args.server_address, args.port)
