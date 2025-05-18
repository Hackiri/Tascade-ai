#!/usr/bin/env python3
"""
Simple MCP client for testing the Tascade AI MCP server with an IDE.

This script provides a simple command-line interface for interacting with
the Tascade AI MCP server. It can be used to test the server functionality
before integrating with an IDE.
"""

import asyncio
import json
import sys
import uuid
import argparse
import websockets
from datetime import datetime


class SimpleMCPClient:
    """Simple client for the Tascade AI MCP server."""
    
    def __init__(self, url="ws://localhost:8765"):
        """
        Initialize the client.
        
        Args:
            url: WebSocket URL of the MCP server
        """
        self.url = url
        self.websocket = None
    
    async def connect(self):
        """Connect to the MCP server."""
        self.websocket = await websockets.connect(self.url)
        print(f"Connected to {self.url}")
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.websocket:
            await self.websocket.close()
            print("Disconnected from server")
    
    async def send_command(self, command, params=None):
        """
        Send a command to the MCP server.
        
        Args:
            command: Command name
            params: Command parameters
        
        Returns:
            Command result
        """
        if not self.websocket:
            raise RuntimeError("Not connected to server")
        
        # Create message
        message = {
            "command": command,
            "params": params or {},
            "id": str(uuid.uuid4())
        }
        
        # Send message
        await self.websocket.send(json.dumps(message))
        print(f"Sent command: {command}")
        
        # Receive response
        response = await self.websocket.recv()
        response_data = json.loads(response)
        
        # Check for error
        if response_data.get("error"):
            error = response_data["error"]
            print(f"Error: {error['message']} (Code: {error['code']})")
            return None
        
        # Return result
        return response_data.get("result")


async def interactive_mode(client):
    """
    Run the client in interactive mode.
    
    Args:
        client: MCP client
    """
    print("Interactive mode. Type 'help' for available commands, 'exit' to quit.")
    
    # Get server info
    info = await client.send_command("get-server-info")
    print(f"Server: {info['name']} v{info['version']}")
    print(f"Available commands: {', '.join(info['commands'])}")
    
    # Command help
    command_help = {
        "get-server-info": "Get information about the server",
        "get-tasks": "Get all tasks",
        "get-task": "Get a specific task by ID",
        "add-task": "Add a new task",
        "update-task": "Update an existing task",
        "delete-task": "Delete a task",
        "get-time-entries": "Get time entries",
        "add-time-entry": "Add a new time entry",
        "start-tracking": "Start time tracking",
        "stop-tracking": "Stop time tracking",
        "help": "Show this help message",
        "exit": "Exit the client"
    }
    
    while True:
        # Get command
        command = input("\nEnter command: ").strip()
        
        if command == "exit":
            break
        
        if command == "help":
            print("\nAvailable commands:")
            for cmd, desc in command_help.items():
                print(f"  {cmd}: {desc}")
            continue
        
        if command not in command_help:
            print(f"Unknown command: {command}")
            continue
        
        # Get parameters
        params = {}
        
        if command == "get-task":
            task_id = input("Enter task ID: ").strip()
            params["id"] = task_id
        
        elif command == "add-task":
            title = input("Enter task title: ").strip()
            description = input("Enter task description: ").strip()
            priority = input("Enter task priority (high/medium/low): ").strip() or "medium"
            
            params["title"] = title
            params["description"] = description
            params["priority"] = priority
        
        elif command == "update-task":
            task_id = input("Enter task ID: ").strip()
            title = input("Enter new title (leave empty to keep current): ").strip()
            description = input("Enter new description (leave empty to keep current): ").strip()
            
            params["id"] = task_id
            
            if title:
                params["title"] = title
            
            if description:
                params["description"] = description
        
        elif command == "delete-task":
            task_id = input("Enter task ID: ").strip()
            params["id"] = task_id
        
        elif command == "get-time-entries":
            task_id = input("Enter task ID (leave empty for all): ").strip()
            
            if task_id:
                params["task_id"] = task_id
        
        elif command == "add-time-entry":
            task_id = input("Enter task ID: ").strip()
            description = input("Enter description: ").strip()
            
            params["task_id"] = task_id
            params["description"] = description
        
        elif command == "start-tracking":
            task_id = input("Enter task ID: ").strip()
            description = input("Enter description: ").strip()
            
            params["task_id"] = task_id
            params["description"] = description
        
        elif command == "stop-tracking":
            session_id = input("Enter session ID: ").strip()
            params["session_id"] = session_id
        
        # Send command
        try:
            result = await client.send_command(command, params)
            
            if result:
                print("\nResult:")
                print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: {e}")


async def main():
    """Main function."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Simple MCP Client")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    
    args = parser.parse_args()
    
    # Create client
    url = f"ws://{args.host}:{args.port}"
    client = SimpleMCPClient(url)
    
    try:
        # Connect to server
        await client.connect()
        
        # Run interactive mode
        await interactive_mode(client)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Disconnect from server
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
