import socket
import threading
import os
import json
import hashlib
import random
from concurrent.futures import ThreadPoolExecutor

CHUNK_SIZE = 1024 * 1024  # 1MB
MAX_RETRIES = 3

def recv_all(sock, size):
    data = b""
    while len(data) < size:
        packet = sock.recv(min(size - len(data), 4096))
        if not packet:
            raise ConnectionError("Incomplete data received")
        data += packet
    return data

def register_file(tracker_host, tracker_port, file, my_port):
    if not os.path.exists(f"{os.environ.get('SHARED_DIR')}/{file}"):
        print(f"File not found in {os.environ.get('SHARED_DIR')}")
        return

    file_size = os.path.getsize(f"{os.environ.get('SHARED_DIR')}/{file}")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((tracker_host, tracker_port))
    s.send(json.dumps({
        "type": "register",
        "file": file,
        "port": my_port,
        "size": file_size
    }).encode())
    print(s.recv(4096).decode())
    s.close()

def get_peers(tracker_host, tracker_port, file):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((tracker_host, tracker_port))
    s.send(json.dumps({"type": "get_peers", "file": file}).encode())
    response = json.loads(s.recv(4096).decode())
    s.close()
    return response

def send_file(conn, file):
    try:
        chunk_index = conn.recv(8)
        if not chunk_index:
            return
        index = int.from_bytes(chunk_index, "big")
        with open(file, "rb") as f:
            f.seek(index * CHUNK_SIZE)
            data = f.read(CHUNK_SIZE)
            checksum = hashlib.sha256(data).hexdigest().encode()
            print(f"Sending chunk {index}, size={len(data)}, checksum={checksum.decode()}")
            conn.send(len(data).to_bytes(4, "big") + data + checksum)
    except Exception as e:
        print("Send error:", e)
    finally:
        conn.close()

def start_server(file_dir, my_port):
    def handler(conn, _):
        file = conn.recv(1024).decode().strip("\x00")
        send_file(conn, os.path.join(file_dir, file))

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", my_port))
    server.listen(5)
    print(f"Peer server running on port {my_port}")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handler, args=(conn, addr), daemon=True).start()

def download_chunk(peer, file, index, chunk_dir):
    for attempt in range(MAX_RETRIES):
        try:
            ip, port = peer
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            s.sendall(file.encode().ljust(1024, b'\x00'))  # pad file name to 1024 bytes
            s.sendall(index.to_bytes(8, "big"))

            size = int.from_bytes(recv_all(s, 4), "big")
            data = recv_all(s, size)
            checksum = recv_all(s, 64)

            if hashlib.sha256(data).hexdigest().encode() == checksum:
                with open(f"{chunk_dir}/{index}.chunk", "wb") as f:
                    f.write(data)
                break
            else:
                print(f"Checksum failed for chunk {index} from {ip}:{port}, retrying...")
            s.close()
        except Exception as e:
            print(f"Download failed for chunk {index}, attempt {attempt+1}: {e}")

def merge_chunks(file, chunk_dir, total_chunks):
    with open(file, "wb") as outfile:
        for i in range(total_chunks):
            chunk_path = f"{chunk_dir}/{i}.chunk"
            if not os.path.exists(chunk_path):
                raise FileNotFoundError(f"Missing chunk: {chunk_path}")
            with open(chunk_path, "rb") as chunk:
                outfile.write(chunk.read())

def download_file(file, tracker_host, tracker_port, chunk_dir="chunks"):
    response = get_peers(tracker_host, tracker_port, file)
    peers = response["peers"]
    file_size = response["size"]

    if not peers:
        print("No peers found for this file.")
        return

    total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
    os.makedirs(chunk_dir, exist_ok=True)

    with ThreadPoolExecutor(max_workers=4) as executor:
        for i in range(total_chunks):
            peer = random.choice(peers)
            executor.submit(download_chunk, peer, file, i, chunk_dir)

    merge_chunks("downloaded_" + file, chunk_dir, total_chunks)
