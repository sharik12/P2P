import argparse
import threading
import os
from peer import start_server, register_file, download_file
from tracker import start_tracker

def run_tracker(args):
    start_tracker(args.host, args.port)

def run_peer_server(args):
    if not os.path.exists(args.dir):
        print(f"Directory '{args.dir}' not found.")
        return
    threading.Thread(target=start_server, args=(args.dir, args.port), daemon=True).start()
    print("Press Ctrl+C to stop the peer server.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nPeer server stopped.")

def run_register(args):
    register_file(args.tracker_host, args.tracker_port, args.filename, args.my_port)

def run_download(args):
    download_file(args.filename, args.tracker_host, args.tracker_port)

def main():
    parser = argparse.ArgumentParser(description="P2P File Sharing CLI")
    subparsers = parser.add_subparsers(dest="command")

    tracker_parser = subparsers.add_parser("tracker", help="Start the tracker server")
    tracker_parser.add_argument("--host", default="0.0.0.0", help="Tracker host")
    tracker_parser.add_argument("--port", type=int, default=8000, help="Tracker port")
    tracker_parser.set_defaults(func=run_tracker)

    peer_parser = subparsers.add_parser("serve", help="Start a peer server")
    peer_parser.add_argument("--dir", default=os.environ.get('SHARED_DIR'), help="Directory for shared files")
    peer_parser.add_argument("--port", type=int, default=9001, help="Peer port")
    peer_parser.set_defaults(func=run_peer_server)

    reg_parser = subparsers.add_parser("register", help="Register a file")
    reg_parser.add_argument("filename", help="File name")
    reg_parser.add_argument("--tracker-host", default="localhost", help="Tracker host")
    reg_parser.add_argument("--tracker-port", type=int, default=8000, help="Tracker port")
    reg_parser.add_argument("--my-port", type=int, default=9001, help="Your peer port")
    reg_parser.set_defaults(func=run_register)

    down_parser = subparsers.add_parser("download", help="Download a file")
    down_parser.add_argument("filename", help="File name")
    down_parser.add_argument("--tracker-host", default="localhost", help="Tracker host")
    down_parser.add_argument("--tracker-port", type=int, default=8000, help="Tracker port")
    down_parser.set_defaults(func=run_download)

    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
