#!/bin/bash
# Check container logs

echo "=== Container Status ==="
docker ps -a | grep monitoring

echo -e "\n=== Last 50 lines of logs ==="
docker logs monitoring-system --tail 50

echo -e "\n=== Checking port 5000 ==="
netstat -tulpn | grep 5000 || echo "Port 5000 not listening"

