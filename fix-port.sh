#!/bin/bash
# Fix port 5000 conflict

echo "Stopping all containers..."
docker stop $(docker ps -aq) 2>/dev/null || true

echo "Removing monitoring-system containers..."
docker rm -f monitoring-system 2>/dev/null || true
docker rm -f webrtc-python-server 2>/dev/null || true

echo "Killing processes on port 5000..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
fuser -k 5000/tcp 2>/dev/null || true

echo "Waiting 3 seconds..."
sleep 3

echo "Checking port 5000..."
if lsof -i:5000; then
    echo "ERROR: Port 5000 still in use!"
    exit 1
else
    echo "SUCCESS: Port 5000 is free!"
fi

