import sys
import socket
import select

# TODO: Parsing of commands sent by client

def broadcast(users_online, up, msg):
    tmp = {}
    for key, value in up.items():
        tmp[key] = value[0]

    for uname in users_online:
        s = tmp.index(uname)
        try:
            s.send(msg.encode('ascii'))
        except:
            print("Error in brosdcasting to user {0}".format(uname))

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
                        if usr in users_online:
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
                            s.send('Incorrect password. Please try again'.encode('ascii'))
                            num_login_attempts[up[s][0]] += 1 # TODO: Block IP
                        else:
                            users_online.append(up[s][0])

                    else:
                    # TODO: Do something with the data
                        print(data.decode())
                else:
                    # broken socket
                    if s in socket_list:
                        socket_list.remove(s)
                        del clients[s]
                        users_online.remove(up[s][0])
                        del up[s]
            except:
                # Some exception has occurred
                # TODO: Do exception handling
                print()
                continue

serv_sock.close()


