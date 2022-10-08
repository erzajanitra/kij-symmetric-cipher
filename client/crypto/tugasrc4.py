# use same key to encrypt and decrypt

def pseudorandom_generator(key):
    p_key = [i for i in range(0, 256)]
    
    i = 0
    for j in range(0, 256):
        i = (i + p_key[j] + key[j % len(key)]) % 256
        
        # swap j to i, then i to j
        p_key[i], p_key[j] = p_key[j], p_key[i]
        # tmp = p_key[j]
        # p_key[j] = p_key[i]
        # p_key[i] = tmp
       
    return p_key
    

def encryption(sched):
    i = 0
    j = 0
    while True:
        i = (1 + i) % 256
        j = (sched[i] + j) % 256
        
        # swap j to i, then i to j
        sched[i], sched[j] = sched[j], sched[i]
        # tmp = sched[j]
        # sched[j] = sched[i]
        # sched[i] = tmp
        
        yield sched[(sched[i] + sched[j]) % 256]        


def encrypt(text, key):
    # ord : turn char into integer
    # text = [ord(char) for char in text]
    key = [ord(char) for char in key]
    
    # prng the key then encrypt
    sched = pseudorandom_generator(key)
    key_stream = encryption(sched)
    
    ciphertext = bytearray()
    for char in text:
        # turn number into hexadecimal value
        enc = (char ^ next(key_stream))
        ciphertext.append(enc)
        
    return ciphertext
    

def decrypt(ciphertext, key):
    key = [ord(char) for char in key]
    
    sched = pseudorandom_generator(key)
    key_stream = encryption(sched)
    
    plaintext = bytearray()
    for char in ciphertext:
        dec = (char ^ next(key_stream))
        plaintext.append(dec)
    
    return plaintext

# input plain text, public key
if __name__ == '__main__':
    # TO DO
    # Constant key for all encryption/decryption algorithms
    private_key='kijpakbasasik'
    ed = input('Enter E for Encrypt, or D for Decrypt: ').upper()
    if ed == 'E':
        # TO DO
        # Dynamic file input and integrate with server socket
        with open('./crypto/1.png', 'rb') as plaintext_file:
          plaintext = plaintext_file.read()

        ciphertext = encrypt(plaintext, private_key) 
        f = open('encrypted.dat', 'wb')
        f.write(ciphertext)
        f.close()
    elif ed == 'D': 
        with open('./crypto/encrypted.dat', 'rb') as ciphertext_file:
          encrypted_file = ciphertext_file.read()

        plaintext = decrypt(encrypted_file, private_key)
        f = open('./crypto/decrypted.dat', 'wb')
        f.write(plaintext)
        f.close()
    else:
        print('Input Error !')