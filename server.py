# 
# Columbia University - CSEE 4119 Computer Networks
# Assignment 1 - Adaptive video streaming
#
# server.py - the server program for taking request from the client and 
#             send the requested file back to the client
#

import socket
import os
import sys

def send_chunk(connection, chunk_path):
    """
    helper function for server to send video files 
    and manifest file to client in a loop

    arguments: 
    connection -- the socket for connection 
    chunk_path -- filepath to requested video file
    """

    with open(chunk_path, 'rb') as chunk_file:
        chunk_data = chunk_file.read(1024)
        while chunk_data:
            connection.sendall(chunk_data)
            chunk_data = chunk_file.read(1024)

def server(listen_port):
    """
    the server function

    arguments:
    listen_port -- user-specified port number that server will listen on
    """

    # establishing connection, listening on port
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', listen_port))
    server_socket.listen(1)

    # accepting a client
    connection, client_address = server_socket.accept()

    try:
        # try to keep recieving requests from client
        while True:
            try:
                request = connection.recv(1024).decode('utf-8')
                if not request:
                    break

                if request.startswith("GET"):
                    # extracting information from request
                    chunk_info = request.split()[1][1:]
                    chunk_path = f".{chunk_info}"
                    # sending request to helper if file exists
                    if os.path.exists(chunk_path):
                        send_chunk(connection, chunk_path)
                    # sending file not found if file not found
                    else:
                        connection.sendall("HTTP/1.1 404 Not Found\n\nChunk not found".encode('utf-8'))
            # error message if client disconnects
            except (OSError, ConnectionResetError):
                print("client disconnected.")
    
    finally:
        # closing connection
        connection.close()

if __name__ == '__main__':
    listen_port = int(sys.argv[1])
    server(listen_port)
