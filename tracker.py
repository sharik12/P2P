import socket
import threading
import json
import os

TRACKER_DB = "peers.json"
file_registry = {}  # filename -> { "size": int, "peers": set() }

registry_lock = threading.Lock()

# Load from disk
if os.path.exists(TRACKER_DB):
    with open(TRACKER_DB, "r") as f:
        raw = json.load(f)
        file_registry = {
            k: {"size": v["size"], "peers": set(tuple(p) for p in v["peers"])}
            for k, v in raw.items()
        }

def save_registry():
    with open(TRACKER_DB, "w") as f:
        json.dump({
            k: {"size": v["size"], "peers": list(v["peers"])}
            for k, v in file_registry.items()
        }, f)

def handle_client(conn, addr):
    try:
        data = conn.recv(4096).decode()
        request = json.loads(data)

        if request["type"] == "register":
            file = request["file"]
            port = request["port"]
            size = request["size"]

            with registry_lock:
                if file not in file_registry:
                    file_registry[file] = {"size": size, "peers": set()}
                file_registry[file]["peers"].add((addr[0], port))
                save_registry()

            conn.send(json.dumps({"status": "registered"}).encode())

        elif request["type"] == "get_peers":
            file = request["file"]
            info = file_registry.get(file)
            if info:
                conn.send(json.dumps({
                    "peers": list(info["peers"]),
                    "size": info["size"]
                }).encode())
            else:
                conn.send(json.dumps({"peers": [], "size": 0}).encode())

    except Exception as e:
        print("Error:", e)
    finally:
        conn.close()

def start_tracker(host="0.0.0.0", port=8000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Tracker running on {host}:{port}")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_tracker()
