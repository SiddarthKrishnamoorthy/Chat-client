import sys
import socket
import select
import signal
import re
from Crypto.Util import number
from Crypto import Random
from Crypto.Cipher import AES
import base64
import hashlib

class AESCipher(object):

    def __init__(self, key): 
        self.bs = 32
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

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
g, p, a, b, g_a, g_ab = 0,0,0,-1,0,0
while True:
    if ctr == 3:
        s.close()
        sys.exit(0)

    socket_list = [sys.stdin, s]

    pi = re.compile('^([a-z]+) ([0-9]+),([0-9]+),([0-9]+)$')
    pr = re.compile('^([a-z]+) ([0-9]+)$')
    # Getting readable socket lists
    ready_to_read, ready_to_write, in_error = select.select(socket_list, [], [])
    for sock in ready_to_read:
        if sock == s:
            # data coming from server
            data = sock.recv(1000)
            #print(data.decode())
            if data:
                if data.decode() == 'logout':
                    s.close()
                    sys.exit(0)
                if data.decode() == 'Incorrect username/password. Please try again':
                    print("Incorrect username/password. Please try again")
                    username = input("Enter username: ")
                    s.send(username.encode())
                    password = input("Enter password: ")
                    s.send(password.encode())
                    sys.stdout.write('> ')
                    sys.stdout.flush()
                elif data.decode() == 'Your IP is blocked':
                    print('Your IP is blocked')
                    s.close()
                    sys.exit(1)
                elif pi.match(data.decode()):
                    b = number.getRandomInteger(10)
                    dat = data.decode()
                    _, dat = dat.split(' ')
                    g, p, g_a = dat.split(',')
                    g = int(g)
                    p = int(p)
                    g_b = pow(g, b, p)
                    s.send((data.decode().split(' ')[0] + ' '+ str(g_b)).encode('ascii'))
                    g_ab = pow(int(g_a), b, p)
                    #print(g_ab)
                elif data.decode() == 'Cannot send encrypted message':
                    sys.stdout.write('\n' + data.decode() + '\n')
                    sys.stdout.flush()
                    sys.stdout.write('> ')
                    sys.stdout.flush()
                elif 'Can send' in data.decode():
                    g = number.getPrime(50)
                    p = number.getPrime(50)
                    a = number.getRandomInteger(10)
                    sk = data.decode().split(' ')
                    g2 = pow(g, a, p)
                    #print(sk[2])
                    s.send((sk[2] + ' ' + str(g) + ',' + str(p) + ',' + str(g2)).encode('ascii'))
                elif pr.match(data.decode()):
                    send, g3 = data.decode().split(' ')
                    g3 = int(g3)
                    g_ab = pow(g3, a, p)
                    #print(g_ab)
                elif 'secret' in data.decode(): # TODO: Implement
                    _, sdr, msg = data.decode().split(' ')
                    aes = AESCipher(str(g_ab))
                    dec_msg = aes.decrypt(msg.encode())
                    sys.stdout.write('\n***'+sdr+'*** ' + dec_msg.split(' ')[2]+'\n')
                    sys.stdout.flush()
                    sys.stdout.write('> ')
                    sys.stdout.flush()
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
            ptr = re.compile("^(enc)") # encrypted message command
            p = re.compile('^([0-9]+),([0-9]+)$')
            ptr2 = re.compile("^(secret)")
            if ptr.match(msg):
                ms = msg.split(' ')
                st = ms[0] + ' ' + ms[1]
                #print(st)
                s.send(st.encode('ascii'))
            elif ptr2.match(msg):
                _, sdr, mg = msg.split(' ')
                aes = AESCipher(str(g_ab))
                enc_msg = aes.encrypt(msg)
                s.send(('secret ' + sdr + ' ').encode('ascii') + enc_msg)
            else:
                s.send(msg.encode('ascii'))
            #sys.stdout.write('> ')
            #sys.stdout.flush()


