import sys
import socket
import select
import time
import calendar
import signal
import os
import re

def signal_handler(signum, frame):
    print('Signal called with signal ', signum)
    # Exit gracefully
    while users_online:
        usr = users_online.pop()
        usr.sock.close()

    serv_sock.close()
    sys.exit(0)

class Client:
    def __init__(self, sock, username):
        self.sock = sock
        self.login_time = calendar.timegm(time.gmtime())
        self.uname = username

    def __str__(self):
        return self.uname

    __repr__ = __str__

# TODO: Parsing of commands sent by client
def cmd(msg, users_online, up, sock):
    ms = msg.strip().split(' ')
    cmds = ms[0]
    print(cmds)
    p = re.compile('^([a-z]+) ([0-9]+),([0-9]+),([0-9]+)$')
    p2 = re.compile('^([a-z]+) ([0-9]+)$')
    print(msg)

    if cmds == 'whoelse\n':
        string = '\n'.join([x.uname for x in users_online])
        #print(string)
        sock.send(string.encode('ascii'))
    elif cmds == 'wholasthr\n':
        ms = []
        t = calendar.timegm(time.gmtime())
        for u in users_online:
            if t - u.login_time <= 3600:
                ms.append(u.uname)
        string = '\n'.join(x for x in ms)
        sock.send(string.encode('ascii'))
        #print(string)
    elif cmds == 'broadcast':
        #print(ms[1])
        t = next(x for x in users_online if x.sock == sock)
        message = '\n**' + t.uname + ' broadcasts** ' + ms[1]
        broadcast(users_online, up, message, sock) # TODO: Remove \n at the end of the string
    elif cmds == 'message':
        t = next(x for x in users_online if x.sock == sock)
        uname = ms[1]
        if (uname in blockedUsers) and (t.uname in blockedUsers[uname]):
            sock.send(("You have been blocked by " + uname).encode('ascii'))
            return
        message = '*' + t.uname  + '* ' + ms[2]

        for x in users_online:
            if x.uname == uname:
                x.sock.send(message.encode('ascii'))
            else:
                with open(uname, 'a+') as file:
                    file.write('\n' + message)
    elif cmds == 'enc':
        uname = ms[1]
        sender = next(x for x in users_online if x.sock == sock)
        recvr = next(x for x in users_online if x.uname == uname)

        if recvr is not None:
            sock.send(('Can send ' + recvr.uname).encode('ascii'))
            #print('ssend')
        else:
            sock.send('Cannot send encrypted message'.encode('ascii'))
            #print('1ssend')
            return
    elif p.match(msg) or p2.match(msg):
        #print(msg)
        recv, dt = msg.split(' ')
        recvr = next(x for x in users_online if x.uname == recv)
        sender = next(x for x in users_online if x.sock == sock)
        #print(recvr.uname)
        sk = sender.uname + ' ' + dt
        recvr.sock.send(sk.encode('ascii'))
    elif cmds == 'secret': 
        recv = ms[1]
        mg = ms[2]
        recvr = next(x for x in users_online if x.uname == recv)
        sender = next(x for x in users_online if x.sock == sock)
        #print(recvr.uname)
        #print(mg)
        recvr.sock.send(('secret ' + sender.uname + ' ' + mg).encode('ascii'))
    elif cmds == 'block':
        recv = ms[1]
        sender = next(x for x in users_online if x.sock == sock)
        if sender.uname not in blockedUsers:
            blockedUsers[sender.uname] = []
        if recv in blockedUsers[sender.uname]:
            sock.send(("User " + recv + " is already blocked").encode('ascii'))
        else:
            blockedUsers[sender.uname].append(recv)
            sock.send(("User " + recv + " is blocked").encode('ascii'))
    elif cmds == 'unblock':
        recv = ms[1]
        sender = next(x for x in users_online if x.sock == sock)
        if sender.uname not in blockedUsers:
            sock.send(("You haven't blocked anyone").encode('ascii'))
        elif recv not in blockedUsers[sender.uname]:
            sock.send(("User " + recv + " is not blocked").encode('ascii'))
        else:
            blockedUsers[sender.uname].remove(recv)
            sock.send(("User " + recv + " is unblocked").encode('ascii'))
    else:
        sock.send('Command not supported'.encode('ascii'))

def broadcast(users_online, up, msg, sock):
    tmp = {}
    for key, value in up.items():
        tmp[key] = value[0]

    for uname in users_online:
        if uname.sock != sock:
            try:
                uname.sock.send(msg.encode('ascii'))
            except:
                print("Error in broadcasting to user {0}".format(uname))

signal.signal(signal.SIGINT, signal_handler)
host = '127.0.0.1'
port = 2000
socket_list = []

serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serv_sock.bind((host, port))
serv_sock.listen(10) # Specifies the max no of queued connections

socket_list.append(serv_sock) # Add serv_sock to list of readable sockets

print('Log:')

clients = {} # Keeps track of number of requests sent by a client
up = {} # Username password key-value for a given socket
users_online = []
num_login_attempts = {}
blockedUsers = {}

while True:
    ready_to_read, ready_to_write, in_err = select.select(socket_list, [], [], 0)

    for s in ready_to_read:
        if s == serv_sock:
            # New connection
            # TODO: Deal with login and sending pending messages when a user logs in again
            sockfd, addr = serv_sock.accept()
            socket_list.append(sockfd) # New connection, added to list of readable sockets
            clients[sockfd] = 0
        else:
            # message sent from a client
            try:
                # parse the client data (in bytes)
                data = s.recv(1000)
                if data:
                    if clients[s] == 0:
                        usr = data.decode()
                        tmp = [x.uname for x in users_online]
                        if usr in tmp:
                            s.send("Already logged in on another terminal".encode('ascii'))
                            continue

                        try:
                            f = open('passwd.db')
                        except:
                            print('passwd.db does not exist')
                            sys.exit(1)

                        # Data parsing in file
                        f = f.read()
                        f = f.split('\n')
                        f.pop()

                        u = [x.split(' ')[0] for x in f]
                        p = [x.split(' ')[1] for x in f]

                        clients[s] += 1
                        if usr not in u:
                            s.send("User not found".encode('ascii'))
                            socket_list.remove(s)
                            del clients[s]
                        else:
                            up[s] = (usr, p[u.index(usr)])

                    elif clients[s] == 1:
                        clients[s] += 1
                        passwd = data.decode()
                        try:
                            f = open('passwd.db')
                        except:
                            print('passwd.db does not exist')
                            sys.exit(1)

                        # Data parsing in file
                        f = f.read()
                        f = f.split('\n')
                        f.pop()

                        if up[s][1] != passwd:
                            s.send('Incorrect username/password. Please try again'.encode('ascii'))
                            num_login_attempts[up[s][0]] += 1 # TODO: Block IP
                        else:
                            user = Client(s, up[s][0])
                            users_online.append(user)
                            try:
                                f = open(user.uname)
                                f = f.read()
                                s.send(f.encode('ascii'))
                                os.remove(user.uname)
                            except:
                                s.send('No pending messages :P'.encode('ascii'))
                            #print(users_online)

                    else:
                        cmd(data.decode(), users_online, up, s)
                        #print(data.decode())
                else:
                    # broken socket
                    if s in socket_list:
                        socket_list.remove(s)
                        del clients[s]
                        users_online.remove(next(x for x in users_online if x.uname == up[s][0]))
                        del up[s]
            except:
                # Some exception has occurred
                # TODO: Do exception handling
                print()
                continue

serv_sock.close()


