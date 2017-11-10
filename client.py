import sys
import socket
import select
import signal
import re
from Crypto.Util import number

def signal_handler(signum, frame):
    print('Signal called with signal ', signum)
    # Exit gracefully
    if s:
        s.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler) # Set signal handler

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
s.send(username.encode())
password = input("Enter password: ")
s.send(password.encode())

sys.stdout.write('> ')
sys.stdout.flush()
ctr = 1
while True:
    if ctr == 3:
        s.close()
        sys.exit(0)

    socket_list = [sys.stdin, s]

    # Getting readable socket lists
    ready_to_read, ready_to_write, in_error = select.select(socket_list, [], [])
    for sock in ready_to_read:
        if sock == s:
            # data coming from server
            data = sock.recv(1000)
            if data:
                if data == 'Incorrect username/password. Please try again':
                    ctr += 1
                elif data == 'Cannot send encrypted message because user is not online':
                    sys.stdout.write('\n' + data.decode() + '\n')
                    sys.stdout.flush()
                    sys.stdout.write('> ')
                    sys.stdout.flush()
                elif data == 'Can send':
                    g = number.getPrime(50)
                    p = number.getPrime(50)
                    s.send((str(g) + ',' + str(p)).encode('ascii'))
                else:
                    sys.stdout.write('\n' + data.decode() + '\n')
                    sys.stdout.flush()
                    sys.stdout.write('> ')
                    sys.stdout.flush()
            else:
                print('Disconnected from server')
                sys.exit(1)
        else:
            msg = sys.stdin.readline()
            '''ptr = re.compile("^(enc)") # encrypted message command
            if ptr.match(msg):
                ms = msg.split(' ')
                st = ms[0] + ' ' + ms[1]
                print(st)
                s.send(st.encode('ascii'))
            else:'''
            s.send(msg.encode('ascii'))
            #sys.stdout.write('> ')
            #sys.stdout.flush()


