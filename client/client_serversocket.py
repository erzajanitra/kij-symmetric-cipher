import math
from pickle import TRUE
import socket
import sys
import os

from tqdm import tqdm

sys.path.append('../')

import header_utils
from exception import FileNotFoundException

import crypto.rc4 as rc4

HEADER = 256
BUFFER_SIZE = 1024
PORT = 5000
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

key = 'kijpakbasasik'

encrpt_function = None

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def get_header():
    header = client.recv(HEADER).decode(FORMAT)
    return header

def recv(header):
    msg_length = header_utils.read_msg_header(header)
    if msg_length:
        msg_length = int(msg_length)
        msg = client.recv(msg_length).decode(FORMAT)
        print(msg)

        return 1
    
    return 0

def send(msg):
    message = msg.encode(FORMAT)
    
    header = header_utils.build_msg_header(message)
    client.send(header)
    client.send(message)

def recv_file(header):
    file_name, file_size = header_utils.read_file_header(header)
    max_loop = math.ceil(file_size / BUFFER_SIZE)
    loop_counter = 0
    with open(f'{file_name}', 'wb') as f:
        with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
          while True:
            data = client.recv(BUFFER_SIZE)
            loop_counter += 1
            f.write(data)
            pbar.update(len(data))
            if loop_counter == max_loop:
                break
            
    f.close()
    print('download success')

def split_byte_chunks(input, chunk_size):
  out_var = bytearray(len(input))
  for chunk in range(0, len(input), chunk_size):
    out_var[chunk : chunk + chunk_size] = input[chunk : chunk + chunk_size]
  
  return out_var


def send_file(filepath, encode):
    if os.path.isfile(filepath):
        file_size = os.path.getsize(filepath)
        file_name = os.path.basename(filepath)
        header = header_utils.build_file_header(file_name, file_size)
        print(f'[SENDING] Client is sending file {file_name} to server')
        client.send(header)
        f = open(filepath, 'rb')
        chunk_data = bytearray()
        
        if encode:
          encoded = encode(f.read(), key)
          chunk_data = split_byte_chunks(encoded, BUFFER_SIZE)
        else:
          chunk_data = split_byte_chunks(f.read(), BUFFER_SIZE)
        
        max_loop = math.ceil(len(chunk_data) / BUFFER_SIZE)
        loop_counter = 0
        with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
          while TRUE:
            data_to_send = chunk_data[loop_counter : loop_counter + BUFFER_SIZE]
            client.send(data_to_send)
            pbar.update(len(data_to_send))
            loop_counter += 1

            if loop_counter == max_loop:
              break
        
        print(f'[SUCCESS] Client successfully send file {file_name} to server')
        f.close()
    else:
        print(f'[ERROR] Client failed to send file {filepath} to server')
        raise FileNotFoundException


def start():
    connected = True
    while connected:
        print(">>", end=' ', flush=True)

        try:
          msg = input()
          if not msg:
            continue
        except KeyboardInterrupt:
          client.close()
          break 
        
        if msg == "quit":
          client.close()
          break

        send(msg)

        if msg.split(" ")[0] == "upload":
          try:

            send_file(msg.split(" ")[1], None)
          except FileNotFoundException:
            send("[ERROR] Client tries to upload invalid filepath")
          continue

        # Get message from server
        header = get_header()
        msg_type = header_utils.read_header_type(header)
        if msg_type == 'file':
            recv_file(header)
        elif msg_type == 'msg':
            recv(header)

start()
