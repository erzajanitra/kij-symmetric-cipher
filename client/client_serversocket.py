from calendar import c
import math
from pickle import TRUE
from posixpath import splitext
import socket
import sys
import os
from time import perf_counter, process_time, time
import cv2
import numpy as np

from tqdm import tqdm


sys.path.append('../')

import header_utils
from exception import FileNotFoundException

from crypto.rc4 import RC4
from crypto.DES import DES
from crypto.AESEnc import AESEnc

HEADER = 256
BUFFER_SIZE = 1024
PORT = 5000
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

class CryptoAlgorithm:
  def __init__(self, name, encrypt, decrypt, ext) -> None:
     self.name = name
     self.encrypt = encrypt
     self.decrypt = decrypt
     self.ext = ext

key = '12345678'
des = DES(key, '12345678')
rc4 = RC4(key)
aes = AESEnc(key+key) 
crypto_algorithms = [
  CryptoAlgorithm('DES', des.encrypt, des.decrypt, '.des'),
  CryptoAlgorithm('RC4', rc4.encrypt, rc4.decrypt, '.rc4'),
  CryptoAlgorithm('AES', aes.encrypt, aes.decrypt, '.aes')
]
current_enc_function = None

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

def is_encrypted(file_name):
    ext = splitext(file_name)[1]
    for crypto in crypto_algorithms:
      if ext == crypto.ext:
        return crypto
    
    return None

def encrypt_to_png(filename, crypto):
    img = cv2.imread(filename)
    # print(img.shape)
    # print(len(img.tobytes()))
    if img.size % 16 > 0:
      row = img.shape[0]
      pad = 16 - (row % 16)
      img = np.pad(img, ((0, pad), (0, 0), (0, 0)))
      img[-1, -1, 0] = pad
    
    img_bytes = img.tobytes()
    enc_img_bytes = crypto.encrypt(img_bytes)
    enc_img = np.frombuffer(enc_img_bytes, np.uint8).reshape(img.shape)
    cv2.imwrite(f'encrypted_{crypto.name}_{filename}', enc_img)

def decrypt_to_png(filename, crypto):
    enc_img = cv2.imread(filename)
    dec_img_bytes = crypto.decrypt(enc_img.tobytes())
    dec_img = np.frombuffer(dec_img_bytes, np.uint8).reshape(enc_img.shape)
    pad = int(dec_img[-1, -1, 0])
    dec_img = dec_img[0:-pad, :, :].copy()
    cv2.imwrite(f'decrypted_{filename}', dec_img)


def recv_file(header):
    filename, file_size = header_utils.read_file_header(header)
    max_loop = math.ceil(file_size / BUFFER_SIZE)
    loop_counter = 0
    with open(f'{filename}', 'wb') as f:
        with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
          while True:
            data = client.recv(BUFFER_SIZE)
            loop_counter += 1
            f.write(data)
            pbar.update(len(data))
            if loop_counter == max_loop:
                break
    f.close()
            
    crypto = is_encrypted(filename)

    if crypto:
      f = open(f'{filename}', 'rb')
      decrypted_filename = splitext(filename)[0]
      decrypted_file = open(f'{decrypted_filename}', 'wb')

      initial_time = time()
      decrypted_data = crypto.decrypt(f.read())
      decrypt_time = time() - initial_time

      print(f"Decryption Process takes about {decrypt_time} seconds")

      decrypted_file.write(decrypted_data)
      decrypted_file.close()
      f.close()

      os.remove(filename)
      filename = decrypted_filename
    
    print(f'[SUCCESS] {filename} successfully downloaded')

def split_byte_chunks(input, chunk_size):
  out_var = bytearray(len(input))
  for chunk in range(0, len(input), chunk_size):
    out_var[chunk : chunk + chunk_size] = input[chunk : chunk + chunk_size]
  
  return out_var


def send_file(filepath, crypto):
    if os.path.isfile(filepath):
        file_size = os.path.getsize(filepath)
        file_name = os.path.basename(filepath)

        f = open(filepath, 'rb')
        header = ''


        if crypto:
          # Kalo mau matiin fungsi image encryptionnya comment aja 2 line dibawah
          if splitext(filepath)[1] == '.png':
            encrypt_to_png(file_name, crypto)
          encrypted_filepath = file_name + crypto.ext

          initial_time = (time(), perf_counter())
          encrypted = crypto.encrypt(f.read())
          encrypt_time = (time() - initial_time[0], perf_counter() - initial_time[1])

          print(f"Encryption Process takes about {encrypt_time[0]} seconds and {encrypt_time[1]} seconds of cpu time")

          encrypted_file = open(encrypted_filepath, 'wb')
          encrypted_file.write(encrypted)
          encrypted_file.close()

          header = header_utils.build_file_header(encrypted_filepath, file_size)

          f = open(encrypted_filepath, 'rb')
        else:
          header = header_utils.build_file_header(file_name, file_size)

        print(f'[SENDING] Client is sending file {file_name} to server')
        client.send(header)

        l = f.read(BUFFER_SIZE)
        
        with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
          while l:
            client.send(l)
            pbar.update(len(l))
            l = f.read(BUFFER_SIZE)
        
        print(f'[SUCCESS] Client successfully send file {file_name} to server')
        f.close()

        if crypto:
          os.remove(encrypted_filepath)
    else:
        print(f'[ERROR] Client failed to send file {filepath} to server')
        raise FileNotFoundException

def command_list():
  print("List of commands\n1. upload\n2. download\n 3.list")

def select_crypto():
  print("Available cryptography algorithms:")
  print("0. DES")
  print("1. RC4")
  print("2. AES")
  print("Select cryptography algorithms by typing their number below:")
  print("Skip by inserting any number to disable cryptography")
  print(">>", end=' ', flush=True)
  c = int(input())
  if c >= 0 and c < len(crypto_algorithms):
    global current_enc_function
    current_enc_function = crypto_algorithms[c]
  else:
    current_enc_function = None


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
            select_crypto()
            send_file(msg.split(" ")[1], current_enc_function)
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
