import argparse
import socket

SIZE = 128
SEND_COUNT = 10


def main(server_address: str, port: int):
  try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      s.connect((server_address, port))
      for i in range(SEND_COUNT):
        s.sendall(b'abcdefghijk')
    print('Client finished.')
  except Exception as e:
    print(e)

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('--server_address', type=str, required=True)
  parser.add_argument('--port', type=int, required=True)
  args = parser.parse_args()
  main(args.server_address, args.port)
