import sys
import socket
import select

host = ''
port = 2000
socket_list = []

serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serv_sock.bind((host, port))
serv_sock.listen(10) # Specifies the max no of queued connections

socket_list.append(serv_sock) # Add serv_sock to list of readable sockets

print('Log:')

while True:
    ready_to_read, ready_to_write, in_err = select.select(socket_list, [], [], 0)

    for s in ready_to_read:
        if s == serv_sock:
            # New connection
            # TODO: Deal with login and other stuff
            sockfd, addr = serv_sock.accept()
            socket_list.append(sockfd) # New connection, added to list of readable sockets
        else:
            # message sent from a client
            try:
                # parse the client data
                data = s.recv(1000)
                if data:
                    # TODO: Do something with the data
                    print()
                else:
                    # broken socket
                    if s in socket_list:
                        socket_list.remove(s)
            except:
                # Some exception has occurred
                # TODO: Do exception handling
                print()
                continue

serv_sock.close()


