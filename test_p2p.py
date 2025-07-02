import unittest
import os
import shutil
import threading
import socket
import json
import time
from peer import start_server, register_file, download_file
from tracker import start_tracker

TRACKER_HOST = "localhost"
TRACKER_PORT = 8500
PEER_PORT = 9500
SHARED_DIR = "test_shared"
CHUNK_DIR = "test_chunks"
TEST_FILE = "testfile.txt"
DOWNLOADED_FILE = "downloaded_" + TEST_FILE

os.environ["SHARED_DIR"] = SHARED_DIR

class TestP2PSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(SHARED_DIR, exist_ok=True)
        with open(f"{SHARED_DIR}/{TEST_FILE}", "w") as f:
            f.write("Hello, this is a test file for P2P sharing." * 1000)  # ~44KB

        # Start tracker
        cls.tracker_thread = threading.Thread(target=start_tracker, args=(TRACKER_HOST, TRACKER_PORT), daemon=True)
        cls.tracker_thread.start()

        # Start peer server
        cls.peer_thread = threading.Thread(target=start_server, args=(SHARED_DIR, PEER_PORT), daemon=True)
        cls.peer_thread.start()

        # Allow some time for servers to start
        import time
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(DOWNLOADED_FILE):
            os.remove(DOWNLOADED_FILE)
        shutil.rmtree(SHARED_DIR, ignore_errors=True)
        shutil.rmtree(CHUNK_DIR, ignore_errors=True)
        if os.path.exists("peers.json"):
            os.remove("peers.json")

    def test_register_and_download(self):
        register_file(TRACKER_HOST, TRACKER_PORT, TEST_FILE, PEER_PORT)
        download_file(TEST_FILE, TRACKER_HOST, TRACKER_PORT, CHUNK_DIR)

        # ⏳ Wait up to 5 seconds for the file to appear
        for _ in range(50):  # 50 x 0.1s = 5 seconds
            if os.path.exists(DOWNLOADED_FILE):
                break
            time.sleep(0.1)

        self.assertTrue(os.path.exists(DOWNLOADED_FILE), "Downloaded file not found")

        with open(f"{SHARED_DIR}/{TEST_FILE}", "rb") as f1, open(DOWNLOADED_FILE, "rb") as f2:
            self.assertEqual(f1.read(), f2.read())

if __name__ == "__main__":
    unittest.main()
