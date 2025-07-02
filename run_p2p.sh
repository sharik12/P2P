#!/bin/bash

export SHARED_DIR="shared_dir"

TRACKER_PORT=8000
PEER_PORT=9001
FILE_NAME="file.txt"
SHARED_DIR="shared_dir"
TRACKER_HOST="localhost"

echo "[1] Starting tracker..."
python main.py tracker --port $TRACKER_PORT &
TRACKER_PID=$!
sleep 1

echo "[2] Starting peer server..."
python main.py serve --dir $SHARED_DIR --port $PEER_PORT &
PEER_PID=$!
sleep 1

echo "[3] Registering file: $FILE_NAME"
python main.py register $FILE_NAME --tracker-host $TRACKER_HOST --tracker-port $TRACKER_PORT --my-port $PEER_PORT
sleep 1

echo "[4] Downloading file: $FILE_NAME"
python main.py download $FILE_NAME --tracker-host $TRACKER_HOST --tracker-port $TRACKER_PORT

echo "[5] Done. Cleaning up..."
kill $TRACKER_PID
kill $PEER_PID
