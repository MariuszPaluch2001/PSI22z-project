import argparse
import socket

BUFSIZE = 100
LOCALHOST = "127.0.0.1"

def main(port: int):
  print("Will listen on ", LOCALHOST, ":", port)
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.bind((LOCALHOST, port))
    i = 1
    
    while True:
      data_address = s.recvfrom(BUFSIZE)
      data = data_address[0]
      address = data_address[1]
      print("Message from Client: {}".format(data)) 
      print("Client IP Address: {}".format(address))
      if not data:
        print("Error in datagram?")
        break

      s.sendto(data, address)
      print('sending dgram #', i) 
      i += 1

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('--port', type=int, required=True)
  args = parser.parse_args()
  main(args.port)