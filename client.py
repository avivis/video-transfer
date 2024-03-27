import socket
import threading
from queue import Queue
from video_player import play_chunks
import os
import sys
import time
import xml.etree.ElementTree as ET

def recv_chunk(chunk, client_socket):
    """
    helper function for client to recieve video files 
    and manifest file from server in a loop

    arguments:
    chunk -- an empty bytearray to which recieved bytes will be concatenated 
    client_socket -- the socket for connection 
    """
    client_socket.settimeout(None)

    try:
        while True:
            chunk_data = client_socket.recv(1024)
            if not chunk_data: 
                break
            chunk.extend(chunk_data)

            if len(chunk_data) < 1024:
                break
    except socket.error as e:
        pass

    return chunk

def client(server_addr, server_port, video_name, alpha, chunks_queue):
    """
    the client function
    write your code here

    arguments:
    server_addr -- the address of the server
    server_port -- the port number of the server
    video_name -- the name of the video
    alpha -- the alpha value for exponentially-weighted moving average
    chunks_queue -- the queue for passing the path of the chunks to the video player
    """
    
    # establishing connection
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_addr, server_port))

    # making note of time connection is established
    og_time = time.time()

    try:

        # constructing path for manifest request
        manifest_path = f"./data/{video_name}/manifest.mpd"

        # requesting manifest path
        request = f"GET {manifest_path} HTTP/1.1\nHost: {server_addr}:{server_port}\n\n"
        client_socket.sendall(request.encode('utf-8'))

        # recieving manifest file
        manifest = client_socket.recv(1024).decode('utf-8')
        # if the video does not exist, disconnect
        if "404 Not Found" in manifest:
            print("Video not found.")
            return  

        # parse throug manifest
        root = ET.fromstring(manifest)
        bitrates = [int(rep.get('bandwidth')) for rep in root.findall('.//Representation')]
        media_presentation_duration = float(root.get('mediaPresentationDuration'))
        max_segment_duration = float(root.get('maxSegmentDuration'))
        num_of_chunks = media_presentation_duration/max_segment_duration 

        # using minimum bitrate for first request
        bitrate = min(bitrates)

        # initializing T_current and avg_throughput
        T_current = 0
        avg_throughput = 0

        # creating temp directory
        if not os.path.exists("tmp"):
            os.makedirs("tmp")
        
        # opening a log file
        with open('log.txt', 'w') as log_file:
                log_file.write(f"")
     
        # looping through chunks
        for chunk_number in range(int(num_of_chunks)):

            # making note of pre-request time
            ts = time.time()
            # sending request for chunk
            request = f"GET ./data/{video_name}/chunks/{video_name}_{bitrate}_{chunk_number:05d}.m4s HTTP/1.1\nHost: {server_addr}:{server_port}\n\n"
            client_socket.sendall(request.encode('utf-8'))
    
            # recieving chunk from server
            chunk = bytearray()
            chunk = recv_chunk(chunk, client_socket)
            # making note of time after recieved 
            tf = time.time()

            # time for ABR stuff
            # making note of size of chunk, converting from bytes to bits
            B = len(chunk)  * 8
            # adding chunk to tmp directory
            # with open(f"tmp/{chunk_number}.m4s", "wb") as f:
            #     f.write(chunk)
            # calculating T_new
            T_new = B / (tf - ts)
            # updating T_current and avg_throughput
            T_current = (alpha * T_new) + ((1 - alpha) * T_current)
            avg_throughput = (alpha * T_new) + ((1 - alpha) * avg_throughput)
       
            # updating log file
            # making note of time pre-adding to log
            log_time = time.time()
            # writing to log
            with open('log.txt', 'a') as log_file:
                log_file.write(f"{log_time - og_time} {tf-ts} {T_new} {avg_throughput} {bitrate} {video_name}_{bitrate:06d}_{chunk_number:05d}.m4s\n")
            # choosing bitrate for next time
            for b in bitrates:
                if (avg_throughput >= (1.5*b) ):
                    if (b > bitrate):
                        bitrate = b
                        
    # closing connection
    finally:
        client_socket.close()

    # to visualize the adaptive video streaming, store the chunk in a temporary folder and
    # pass the path of the chunk to the video player
    # 
    # # create temporary directory if not exist
    # if not os.path.exists("tmp"):
    #     os.makedirs("tmp")
    # # write chunk to the temporary directory
    # with open(f"tmp/chunk_0.m4s", "wb") as f:
    #     f.write(chunk)
    # # put the path of the chunk to the queue
    # chunks_queue.put(f"tmp/chunk_0.m4s")

# parse input arguments and pass to the client function
if __name__ == '__main__':
    server_addr = sys.argv[1]
    server_port = int(sys.argv[2])
    video_name = sys.argv[3]
    alpha = float(sys.argv[4])

    # init queue for passing the path of the chunks to the video player
    chunks_queue = Queue()
    # start the client thread with the input arguments
    client_thread = threading.Thread(target = client, args =(server_addr, server_port, video_name, alpha, chunks_queue))
    client_thread.start()
    # start the video player
    # play_chunks(chunks_queue)
