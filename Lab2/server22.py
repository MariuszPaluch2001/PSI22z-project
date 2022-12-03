import argparse
import socket

BUFSIZE = 4
LOCALHOST = "127.0.0.1"

def main(port: int):
  print("Will listen on ", LOCALHOST, ":", port)
  try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      s.bind((LOCALHOST, port))
      s.listen(5)

      while True:
        conn, addr = s.accept()
        with conn:
          print("Connect from: ", addr)
          while True:
            data = conn.recv(BUFSIZE)
            if not data:
              break
            print("Message from Client: {}".format(data.decode("utf-8")))
        conn.close()

  except Exception as e:
    print(e)

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('--port', type=int, required=True)
  args = parser.parse_args()
  main(args.port)
