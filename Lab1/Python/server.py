import argparse
import socket

BUFSIZE = 100
ADDRESS = "0"

def main(port: int):
  print("Will listen on ", ADDRESS, ":", port)
  try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
      s.bind((ADDRESS, port))
      i = 1
      
      while True:
        data_address = s.recvfrom(BUFSIZE)
        data = data_address[0]
        print(data)
        address = data_address[1]
        print("Message from Client: {}".format(data)) 
        print("Client IP Address: {}".format(address))
        if not data:
          print("Error in datagram?")
          break

        s.sendto(data, address)
        print('sending dgram #', i) 
        i += 1
  except Exception as e:
    print(e)

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('--port', type=int, required=True)
  args = parser.parse_args()
  main(args.port)