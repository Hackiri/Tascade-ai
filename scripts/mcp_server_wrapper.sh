#!/bin/bash

# Wrapper script for Tascade AI MCP server
# This script runs the Tascade AI MCP server in a Nix shell

# Function to check if a command exists
check_command() {
  if ! command -v "$1" &> /dev/null; then
    echo "Error: Required command '$1' not found."
    echo "Please make sure it is installed and in your PATH."
    return 1
  fi
  return 0
}

# Check for required commands
check_command nc || echo "Warning: 'nc' command not found. Port conflict detection may not work properly."
check_command node || { echo "Error: 'node' command not found. Please install Node.js to run the MCP server."; exit 1; }

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default port
PORT=8765

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --port|-p)
      PORT="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [--port PORT] [--help]"
      echo ""
      echo "Options:"
      echo "  --port, -p PORT  Specify the port to use (default: 8765)"
      echo "  --help, -h       Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Check if the port is already in use
if nc -z localhost $PORT 2>/dev/null; then
  echo "Port $PORT is already in use."
  echo "You can specify a different port with the --port option."
  echo "For example: $0 --port 8766"
  
  # Try to find a free port automatically
  for try_port in {8766..8775}; do
    if ! nc -z localhost $try_port 2>/dev/null; then
      echo "Found available port: $try_port"
      echo "Starting server on port $try_port instead..."
      PORT=$try_port
      break
    fi
  done
  
  # If we still have the original port, all alternatives were taken
  if [ "$PORT" == "8765" ]; then
    echo "Could not find an available port. Please stop the existing server or specify a different port."
    exit 1
  fi
fi

# Run the Node.js MCP server
echo "Starting Tascade AI MCP server on port $PORT..."
cd "$PROJECT_DIR"
node scripts/node_mcp_server.js --port $PORT
