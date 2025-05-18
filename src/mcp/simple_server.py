#!/usr/bin/env python3
"""
Simplified MCP server implementation for Tascade AI.

This module provides a basic Model Context Protocol (MCP) server for Tascade AI
that can be easily tested with an IDE.
"""

import asyncio
import json
import logging
import os
import sys
import uuid
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tascade.mcp.simple_server")


class SimpleTascadeMCPServer:
    """Simple MCP server for Tascade AI."""
    
    def __init__(self, host="localhost", port=8765):
        """
        Initialize the server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        self.host = host
        self.port = port
        self.tasks = {}  # Simple in-memory task storage
        self.time_entries = {}  # Simple in-memory time entry storage
        
        # Set up command handlers
        self.command_handlers = {
            # Task management commands
            "get-tasks": self._handle_get_tasks,
            "get-task": self._handle_get_task,
            "add-task": self._handle_add_task,
            "update-task": self._handle_update_task,
            "delete-task": self._handle_delete_task,
            
            # Time tracking commands
            "get-time-entries": self._handle_get_time_entries,
            "add-time-entry": self._handle_add_time_entry,
            "start-tracking": self._handle_start_tracking,
            "stop-tracking": self._handle_stop_tracking,
            
            # Server info commands
            "get-server-info": self._handle_get_server_info,
        }
    
    async def start(self):
        """Start the MCP server."""
        logger.info(f"Starting Simple Tascade MCP server on {self.host}:{self.port}")
        
        async with websockets.serve(self._handle_connection, self.host, self.port):
            await asyncio.Future()  # Run forever
    
    async def _handle_connection(self, websocket):
        """
        Handle a WebSocket connection.
        
        Args:
            websocket: WebSocket connection
        """
        client_id = str(uuid.uuid4())
        logger.info(f"Client connected: {client_id}")
        
        try:
            async for message in websocket:
                await self._handle_message(websocket, message, client_id)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error handling connection: {e}")
    
    async def _handle_message(self, websocket, message, client_id):
        """
        Handle a message from a client.
        
        Args:
            websocket: WebSocket connection
            message: Message from client
            client_id: Client identifier
        """
        try:
            # Parse message
            data = json.loads(message)
            
            # Extract command and parameters
            command = data.get("command")
            params = data.get("params", {})
            request_id = data.get("id", str(uuid.uuid4()))
            
            logger.info(f"Received command: {command} (ID: {request_id})")
            
            # Handle command
            if command in self.command_handlers:
                handler = self.command_handlers[command]
                result = await handler(params)
                
                # Send response
                response = {
                    "id": request_id,
                    "result": result,
                    "error": None
                }
            else:
                # Unknown command
                response = {
                    "id": request_id,
                    "result": None,
                    "error": {
                        "code": "unknown_command",
                        "message": f"Unknown command: {command}"
                    }
                }
            
            await websocket.send(json.dumps(response))
        except json.JSONDecodeError:
            # Invalid JSON
            response = {
                "id": None,
                "result": None,
                "error": {
                    "code": "invalid_json",
                    "message": "Invalid JSON message"
                }
            }
            await websocket.send(json.dumps(response))
        except Exception as e:
            # Other error
            logger.error(f"Error handling message: {e}")
            response = {
                "id": None,
                "result": None,
                "error": {
                    "code": "internal_error",
                    "message": str(e)
                }
            }
            await websocket.send(json.dumps(response))
    
    # Task management command handlers
    
    async def _handle_get_tasks(self, params):
        """
        Handle get-tasks command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        status = params.get("status")
        
        # Filter tasks by status if provided
        if status:
            tasks = {
                task_id: task
                for task_id, task in self.tasks.items()
                if task.get("status") == status
            }
        else:
            tasks = self.tasks
        
        return {
            "tasks": list(tasks.values())
        }
    
    async def _handle_get_task(self, params):
        """
        Handle get-task command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        task_id = params.get("id")
        
        if not task_id:
            raise ValueError("Task ID is required")
        
        # Get task
        task = self.tasks.get(task_id)
        
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        return {
            "task": task
        }
    
    async def _handle_add_task(self, params):
        """
        Handle add-task command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        title = params.get("title")
        description = params.get("description", "")
        priority = params.get("priority", "medium")
        status = params.get("status", "pending")
        
        if not title:
            raise ValueError("Task title is required")
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Create task
        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "priority": priority,
            "status": status,
            "created_at": self._get_current_time(),
            "updated_at": self._get_current_time()
        }
        
        # Store task
        self.tasks[task_id] = task
        
        return {
            "id": task_id,
            "task": task
        }
    
    async def _handle_update_task(self, params):
        """
        Handle update-task command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        task_id = params.get("id")
        
        if not task_id:
            raise ValueError("Task ID is required")
        
        # Get task
        task = self.tasks.get(task_id)
        
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        # Update task
        for key, value in params.items():
            if key != "id" and value is not None:
                task[key] = value
        
        # Update timestamp
        task["updated_at"] = self._get_current_time()
        
        return {
            "success": True,
            "task": task
        }
    
    async def _handle_delete_task(self, params):
        """
        Handle delete-task command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        task_id = params.get("id")
        
        if not task_id:
            raise ValueError("Task ID is required")
        
        # Check if task exists
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        # Delete task
        del self.tasks[task_id]
        
        return {
            "success": True
        }
    
    # Time tracking command handlers
    
    async def _handle_get_time_entries(self, params):
        """
        Handle get-time-entries command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        task_id = params.get("task_id")
        
        # Filter time entries by task ID if provided
        if task_id:
            entries = {
                entry_id: entry
                for entry_id, entry in self.time_entries.items()
                if entry.get("task_id") == task_id
            }
        else:
            entries = self.time_entries
        
        return {
            "entries": list(entries.values())
        }
    
    async def _handle_add_time_entry(self, params):
        """
        Handle add-time-entry command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        task_id = params.get("task_id")
        description = params.get("description", "")
        start_time = params.get("start_time", self._get_current_time())
        end_time = params.get("end_time")
        duration_seconds = params.get("duration_seconds")
        
        if not task_id:
            raise ValueError("Task ID is required")
        
        # Check if task exists
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        # Generate entry ID
        entry_id = str(uuid.uuid4())
        
        # Create time entry
        entry = {
            "id": entry_id,
            "task_id": task_id,
            "description": description,
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": duration_seconds,
            "created_at": self._get_current_time()
        }
        
        # Store time entry
        self.time_entries[entry_id] = entry
        
        return {
            "id": entry_id,
            "entry": entry
        }
    
    async def _handle_start_tracking(self, params):
        """
        Handle start-tracking command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        task_id = params.get("task_id")
        description = params.get("description", "")
        
        if not task_id:
            raise ValueError("Task ID is required")
        
        # Check if task exists
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create session
        session = {
            "id": session_id,
            "task_id": task_id,
            "description": description,
            "start_time": self._get_current_time(),
            "status": "active"
        }
        
        # Store session as a time entry
        self.time_entries[session_id] = session
        
        return {
            "session_id": session_id,
            "session": session
        }
    
    async def _handle_stop_tracking(self, params):
        """
        Handle stop-tracking command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        session_id = params.get("session_id")
        
        if not session_id:
            raise ValueError("Session ID is required")
        
        # Get session
        session = self.time_entries.get(session_id)
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if session is active
        if session.get("status") != "active":
            raise ValueError(f"Session is not active: {session_id}")
        
        # Stop session
        session["status"] = "completed"
        session["end_time"] = self._get_current_time()
        
        # Calculate duration
        start_time = session.get("start_time")
        end_time = session.get("end_time")
        
        if start_time and end_time:
            # This is a simplified duration calculation
            # In a real implementation, you would parse the timestamps
            # and calculate the actual duration
            session["duration_seconds"] = 3600  # 1 hour
        
        return {
            "success": True,
            "session": session
        }
    
    # Server info command handlers
    
    async def _handle_get_server_info(self, params):
        """
        Handle get-server-info command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        return {
            "name": "Simple Tascade AI MCP Server",
            "version": "1.0.0",
            "commands": list(self.command_handlers.keys())
        }
    
    # Helper methods
    
    def _get_current_time(self):
        """
        Get the current time as an ISO 8601 string.
        
        Returns:
            Current time
        """
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    """Main entry point."""
    import argparse
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Simple Tascade AI MCP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind to")
    
    args = parser.parse_args()
    
    # Create server
    server = SimpleTascadeMCPServer(
        host=args.host,
        port=args.port
    )
    
    # Start server
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("Server stopped")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
