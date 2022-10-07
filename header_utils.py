HEADER = 256
FORMAT = 'utf-8'

def build_file_header(filename, filesize):
    header = f"type: 'file',\nfile-name: {filename},\nfile-size: {filesize},"
    f_header = str(header).encode(FORMAT)
    f_header += b' ' * (HEADER - len(f_header))
    return f_header

def build_msg_header(msg):
    header = f"type: 'msg',\nfile-name: null,\nfile-size: {len(msg)},"
    f_header = str(header).encode(FORMAT)
    f_header += b' ' * (HEADER - len(f_header))
    return f_header

def read_msg_header(header):
    if not header:
      return
    props = header.split(',')
    msg_len = int(props[2].split(' ')[1])
    return msg_len

def read_file_header(header):
    if not header:
      return
    props = header.split(',')
    file_name = props[1].split(' ')[1]
    file_size = int(props[2].split(' ')[1])
    return (file_name, file_size)

def read_header_type(header):
    if not header:
      return
    props = header.split(',')
    h_type = props[0].split(' ')[1].strip("'")
    return h_type
