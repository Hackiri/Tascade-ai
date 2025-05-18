#!/usr/bin/env python3
"""
MCP client demo for Tascade AI.

This script demonstrates how to connect to the Tascade AI MCP server
from an IDE or other tool.
"""

import asyncio
import json
import sys
import os
import uuid
import websockets
from datetime import datetime, timedelta
import random

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TascadeMCPClient:
    """Client for the Tascade AI MCP server."""
    
    def __init__(self, url: str = "ws://localhost:8765"):
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
    
    async def send_command(self, command: str, params: dict = None):
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


async def demo_task_management(client):
    """
    Demonstrate task management commands.
    
    Args:
        client: MCP client
    """
    print("\n=== Task Management Demo ===\n")
    
    # Get server info
    print("Getting server info...")
    info = await client.send_command("get-server-info")
    print(f"Server: {info['name']} v{info['version']}")
    print(f"Available commands: {', '.join(info['commands'])}")
    
    # Add a task
    print("\nAdding a task...")
    task_result = await client.send_command("add-task", {
        "title": "Test task from MCP client",
        "description": "This task was created using the MCP client",
        "priority": "high"
    })
    
    if task_result:
        task_id = task_result["id"]
        print(f"Task added with ID: {task_id}")
        
        # Get the task
        print("\nGetting task details...")
        task_details = await client.send_command("get-task", {
            "id": task_id
        })
        
        if task_details:
            task = task_details["task"]
            print(f"Task: {task['title']}")
            print(f"Description: {task['description']}")
            print(f"Priority: {task['priority']}")
            print(f"Status: {task['status']}")
        
        # Update the task
        print("\nUpdating task...")
        update_result = await client.send_command("update-task", {
            "id": task_id,
            "description": "Updated description from MCP client"
        })
        
        if update_result and update_result["success"]:
            print("Task updated successfully")
            
            # Get updated task
            task_details = await client.send_command("get-task", {
                "id": task_id
            })
            
            if task_details:
                task = task_details["task"]
                print(f"Updated description: {task['description']}")
        
        # Set task status
        print("\nSetting task status...")
        status_result = await client.send_command("set-task-status", {
            "id": task_id,
            "status": "in-progress"
        })
        
        if status_result and status_result["success"]:
            print("Task status updated successfully")
            
            # Get updated task
            task_details = await client.send_command("get-task", {
                "id": task_id
            })
            
            if task_details:
                task = task_details["task"]
                print(f"Updated status: {task['status']}")
        
        # Get all tasks
        print("\nGetting all tasks...")
        tasks_result = await client.send_command("get-tasks")
        
        if tasks_result:
            tasks = tasks_result["tasks"]
            print(f"Found {len(tasks)} tasks:")
            
            for task in tasks:
                print(f"- {task['id']}: {task['title']} ({task['status']})")


async def demo_time_tracking(client):
    """
    Demonstrate time tracking commands.
    
    Args:
        client: MCP client
    """
    print("\n=== Time Tracking Demo ===\n")
    
    # Add a task for time tracking
    print("Adding a task for time tracking...")
    task_result = await client.send_command("add-task", {
        "title": "Time tracking test task",
        "description": "This task is used for time tracking demo",
        "priority": "medium"
    })
    
    if task_result:
        task_id = task_result["id"]
        print(f"Task added with ID: {task_id}")
        
        # Start tracking
        print("\nStarting time tracking...")
        start_result = await client.send_command("start-tracking", {
            "task_id": task_id,
            "description": "Working on time tracking demo"
        })
        
        if start_result:
            session_id = start_result["session_id"]
            print(f"Session started with ID: {session_id}")
            
            # Get tracking status
            print("\nGetting tracking status...")
            status_result = await client.send_command("get-tracking-status", {})
            
            if status_result:
                if status_result.get("active_session"):
                    session = status_result["active_session"]
                    print(f"Active session: {session['id']}")
                    print(f"Task: {session['task_id']}")
                    print(f"Started at: {session['start_time']}")
                    print(f"Elapsed: {session['elapsed_seconds']} seconds")
                else:
                    print("No active session")
            
            # Pause tracking
            print("\nPausing tracking...")
            await asyncio.sleep(2)  # Wait a bit for demonstration
            
            pause_result = await client.send_command("pause-tracking", {
                "session_id": session_id
            })
            
            if pause_result:
                print("Session paused")
                print(f"Paused at: {pause_result['paused_at']}")
            
            # Resume tracking
            print("\nResuming tracking...")
            await asyncio.sleep(1)  # Wait a bit for demonstration
            
            resume_result = await client.send_command("resume-tracking", {
                "session_id": session_id
            })
            
            if resume_result:
                print("Session resumed")
                print(f"Resumed at: {resume_result['resumed_at']}")
            
            # Stop tracking
            print("\nStopping tracking...")
            await asyncio.sleep(2)  # Wait a bit for demonstration
            
            stop_result = await client.send_command("stop-tracking", {
                "session_id": session_id
            })
            
            if stop_result:
                print("Session stopped")
                print(f"Duration: {stop_result['duration_seconds']} seconds")
                print(f"Time entry created with ID: {stop_result['entry_id']}")
            
            # Get time entries
            print("\nGetting time entries...")
            entries_result = await client.send_command("get-time-entries", {
                "task_id": task_id
            })
            
            if entries_result:
                entries = entries_result["entries"]
                print(f"Found {len(entries)} time entries:")
                
                for entry in entries:
                    print(f"- {entry['id']}: {entry['description']} ({entry['duration_seconds']} seconds)")


async def demo_visualization(client):
    """
    Demonstrate visualization commands.
    
    Args:
        client: MCP client
    """
    print("\n=== Visualization Demo ===\n")
    
    # Generate sample time entries
    print("Generating sample time entries...")
    
    # Generate task IDs
    task_ids = ["task_1", "task_2", "task_3", "task_4", "task_5"]
    
    # Generate task names
    task_names = {
        "task_1": "Feature Development",
        "task_2": "Bug Fixing",
        "task_3": "Documentation",
        "task_4": "Testing",
        "task_5": "Meetings"
    }
    
    # Generate categories
    categories = ["Development", "Planning", "Research", "Communication"]
    
    # Generate time entries
    time_entries = []
    
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    for i in range(100):
        # Random task
        task_id = random.choice(task_ids)
        
        # Random category
        category = random.choice(categories)
        
        # Random date between start and end
        days_range = (end_date - start_date).days
        random_days = random.randint(0, days_range)
        entry_date = start_date + timedelta(days=random_days)
        
        # Random time
        hour = random.randint(8, 17)
        minute = random.randint(0, 59)
        entry_date = entry_date.replace(hour=hour, minute=minute)
        
        # Random duration (15 minutes to 3 hours)
        duration_minutes = random.randint(15, 180)
        duration_seconds = duration_minutes * 60
        
        # End time
        end_time = entry_date + timedelta(minutes=duration_minutes)
        
        # Create entry
        entry = {
            "id": f"entry_{i}",
            "task_id": task_id,
            "task_name": task_names.get(task_id, task_id),
            "category": category,
            "start_time": entry_date.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration_seconds,
            "description": f"Working on {task_names.get(task_id, task_id)}",
            "completed": random.random() > 0.2  # 80% chance of completion
        }
        
        time_entries.append(entry)
    
    print(f"Generated {len(time_entries)} sample time entries")
    
    # Generate time series visualization
    print("\nGenerating time series visualization...")
    
    viz_result = await client.send_command("generate-visualization", {
        "type": "time_series",
        "data": time_entries,
        "options": {
            "time_field": "start_time",
            "value_field": "duration_seconds",
            "category_field": "task_name",
            "chart_type": "line",
            "time_grouping": "daily",
            "title": "Time Spent by Task",
            "subtitle": "Daily time tracking data",
            "stacked": False,
            "show_markers": True
        }
    })
    
    if viz_result:
        print("Time series visualization generated")
        print(f"Image data length: {len(viz_result['image'])} bytes")
        
        # Save image to file
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'mcp_demo')
        os.makedirs(output_dir, exist_ok=True)
        
        with open(os.path.join(output_dir, "time_series.png"), "wb") as f:
            import base64
            f.write(base64.b64decode(viz_result["image"]))
        
        print(f"Image saved to: {os.path.join(output_dir, 'time_series.png')}")
    
    # Generate dashboard
    print("\nGenerating dashboard...")
    
    dashboard_result = await client.send_command("generate-dashboard", {
        "title": "Tascade AI MCP Dashboard",
        "layout": "grid",
        "theme": "light",
        "panels": [
            {
                "type": "time_series",
                "title": "Time Spent by Task",
                "data": time_entries,
                "options": {
                    "time_field": "start_time",
                    "value_field": "duration_seconds",
                    "category_field": "task_name",
                    "chart_type": "line",
                    "time_grouping": "daily",
                    "width": 2,
                    "height": 1
                }
            },
            {
                "type": "task_distribution",
                "title": "Time Distribution",
                "data": time_entries,
                "options": {
                    "task_field": "task_name",
                    "value_field": "duration_seconds",
                    "chart_type": "pie",
                    "width": 1,
                    "height": 1
                }
            }
        ]
    })
    
    if dashboard_result:
        print("Dashboard generated")
        print(f"HTML length: {len(dashboard_result['html'])} bytes")
        
        # Save HTML to file
        with open(os.path.join(output_dir, "dashboard.html"), "w") as f:
            f.write(dashboard_result["html"])
        
        print(f"Dashboard saved to: {os.path.join(output_dir, 'dashboard.html')}")


async def main():
    """Main function."""
    # Create client
    client = TascadeMCPClient()
    
    try:
        # Connect to server
        await client.connect()
        
        # Run demos
        await demo_task_management(client)
        await demo_time_tracking(client)
        await demo_visualization(client)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Disconnect from server
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
