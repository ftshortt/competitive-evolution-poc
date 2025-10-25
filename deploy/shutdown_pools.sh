#!/bin/bash
set -euo pipefail

echo "Starting shutdown process..."

# Kill all processes from PID files
if [ -d "logs" ]; then
  echo "Stopping pool processes..."
  for pid_file in logs/*.pid; do
    if [ -f "$pid_file" ]; then
      pid=$(cat "$pid_file" || true)
      if [ -n "$pid" ]; then
        echo "Killing process $pid from $pid_file"
        kill "$pid" 2>/dev/null || true
      fi
      echo "Removing $pid_file"
      rm -f "$pid_file" || true
    fi
  done
else
  echo "No logs directory found, skipping PID cleanup"
fi

# Stop infrastructure services
echo "Stopping infrastructure services..."
docker-compose down || true

echo "Shutdown complete"
