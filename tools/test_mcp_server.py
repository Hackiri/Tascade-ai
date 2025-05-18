#!/usr/bin/env python3
"""
Simple script to test the Tascade AI MCP server.
"""

import asyncio
import json
import websockets


async def test_mcp_server():
    """Test the MCP server with a simple command."""
    uri = "ws://localhost:8765"
    
    print(f"Connecting to {uri}...")
    
    async with websockets.connect(uri) as websocket:
        print("Connected!")
        
        # Create a simple command
        command = {
            "command": "get-server-info",
            "params": {},
            "id": "1"
        }
        
        # Send the command
        print(f"Sending command: {json.dumps(command)}")
        await websocket.send(json.dumps(command))
        
        # Receive the response
        response = await websocket.recv()
        response_data = json.loads(response)
        
        print("\nReceived response:")
        print(json.dumps(response_data, indent=2))
        
        # If successful, try adding a task
        if not response_data.get("error"):
            print("\nAdding a task...")
            
            # Create a task command
            task_command = {
                "command": "add-task",
                "params": {
                    "title": "Test task from Python script",
                    "description": "This task was created using a Python script",
                    "priority": "high"
                },
                "id": "2"
            }
            
            # Send the command
            print(f"Sending command: {json.dumps(task_command)}")
            await websocket.send(json.dumps(task_command))
            
            # Receive the response
            task_response = await websocket.recv()
            task_response_data = json.loads(task_response)
            
            print("\nReceived response:")
            print(json.dumps(task_response_data, indent=2))
            
            # If task was added successfully, get all tasks
            if not task_response_data.get("error"):
                task_id = task_response_data.get("result", {}).get("id")
                
                if task_id:
                    print(f"\nTask added with ID: {task_id}")
                    print("Getting all tasks...")
                    
                    # Create a get tasks command
                    get_tasks_command = {
                        "command": "get-tasks",
                        "params": {},
                        "id": "3"
                    }
                    
                    # Send the command
                    print(f"Sending command: {json.dumps(get_tasks_command)}")
                    await websocket.send(json.dumps(get_tasks_command))
                    
                    # Receive the response
                    get_tasks_response = await websocket.recv()
                    get_tasks_response_data = json.loads(get_tasks_response)
                    
                    print("\nReceived response:")
                    print(json.dumps(get_tasks_response_data, indent=2))


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
