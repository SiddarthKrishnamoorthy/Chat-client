import sys
import socket
import select

host = "127.0.0.1" # enter host here
port = 2000 # enter port no here

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2) # Set timeout here

try:
    s.connect((host, port))
except:
    print("Connection failed")
    sys.exit(1)

username = input("Enter username: ")
password = input("Enter password: ")

# TODO: Send username and password, if correct log in, else quit

while True:
    # socket_list = [sys.stdin, s]
    sys.stdout.write('[You] ')
    msg = sys.stdin.readline()
    sys.stdout.flush()


