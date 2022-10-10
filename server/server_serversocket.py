import math
import os
import socket
import socketserver
import sys
import threading
from os import walk

from tqdm import tqdm

sys.path.append('../')
import header_utils
from exception import FileNotFoundException

# Constants
HEADER = 256
BUFFER_SIZE = 1024
PORT = 5000
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
# DATASET = './server/dataset'
DATASET = './dataset'

files = []

def listFiles():
    files = next(walk(DATASET), (None, None, []))[2]
    message = "List of files :\n"
    for idx, f in enumerate(files):
        message += f"{idx} : {f}\n"

    return message

def recv(conn, addr):
  header = conn.recv(HEADER).decode(FORMAT)
  header_type = header_utils.read_header_type(header)
  if header_type == 'msg':
    return recv_message(conn, addr, header)
  elif header_type == 'file':
    return recv_file(conn, addr, header)
  else:
    return None



def send(conn, addr, msg):
    
    message = msg.encode(FORMAT)
    
    header = header_utils.build_msg_header(message)
    print(f'[SENDING] Server is sending {len(msg)} bytes of data to {addr}')
    conn.send(header)
    conn.send(message)



def recv_message(conn, addr, header):
    msg_length = header_utils.read_msg_header(header)
    if msg_length:
        msg_length = int(msg_length)
        msg = conn.recv(msg_length).decode(FORMAT)
        print(f"[{addr}] {msg}")

        if(msg != DISCONNECT_MESSAGE):
            return msg
            
    return None

def send_file(conn, addr, file):
    file_path = f'{DATASET}/{file}'
    if os.path.isfile(file_path):
        file_size = os.path.getsize(file_path)
        header = header_utils.build_file_header(file, file_size)
        print(f'[SENDING] Server is sending file {file} to {addr}')
        conn.send(header)
        f = open(file_path, 'rb')
        l = f.read(1024)
        while l:
            conn.send(l)
            l = f.read(BUFFER_SIZE)
        print(f'[SUCCESS] Server successfully send file {file} to {addr}')
        f.close()
    else:
        print(f'[ERROR] Server failed to send file {file} to {addr}')
        raise FileNotFoundException

def recv_file(conn, addr, header):
    file_name, file_size = header_utils.read_file_header(header)
    max_loop = math.ceil(file_size / BUFFER_SIZE)
    loop_counter = 0
    with open(f'{DATASET}/{file_name}', 'wb') as f:
        print(f'[RECEIVING] Server is receiving file {file_name} from {addr}')
        with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
          while True:

            data = conn.recv(BUFFER_SIZE)
            loop_counter += 1
            f.write(data)
            pbar.update(len(data))
            if loop_counter == max_loop:
                break
            
    f.close()
    print(f'[SUCCESS] Server success receiving file {file_name} from {addr}')
    

def handle_client(conn, addr):
    connected = True
    while connected:
        res = recv(conn, addr)
        if not res:
            connected = False
        else:
            cmd = res.split(' ')
            if cmd[0] == 'download':
                dl_file = cmd[1]
                try:
                  send_file(conn, addr, dl_file)
                except FileNotFoundException:
                  send(conn, addr, "[ERROR] Server cant find your requested file")
            elif cmd[0] == 'upload':
                recv(conn, addr)
            elif cmd[0] == 'list':
                send(conn, addr, f"{listFiles()}Select file you want to download with command 'download nama_file'")
            else:
                send(conn, addr, "Invalid command, please try again")

    print(f'[DISCONNECTED] Client {addr} disconnected')
    conn.close()
    
    return None

class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        print(f"[LISTENING] Server is listening on {self.client_address}")
        while True:
            if not handle_client(self.request,self.client_address):
              break

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def start():
    # server.listen()
    print(f"[NEW CONNECTION] {ADDR} connected.")
    server = ThreadedTCPServer(ADDR, MyTCPHandler)
    with server:
        server.serve_forever()
    
        # thread = threading.Thread(target=handle_client, args=(conn, addr))
        # thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")
        
start()