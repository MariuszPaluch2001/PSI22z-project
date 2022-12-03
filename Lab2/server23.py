import argparse
import socket

BUFSIZE = 128
LOCALHOST = "0"

def main(port: int):
  print("Will listen on ", LOCALHOST, ":", port)
  try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      s.bind((LOCALHOST, port))
      s.listen(5)
      print(f"Listening on: {LOCALHOST}:{port}")

      while True:
        conn, addr = s.accept()
        with conn:
          conn.settimeout(5)
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
