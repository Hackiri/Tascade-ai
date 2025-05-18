"""
MCP server implementation for Tascade AI.

This module provides a Model Context Protocol (MCP) server for Tascade AI,
enabling IDE integration and other tool interactions.
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Any, Optional, Union, Callable
import uuid
import asyncio
import websockets
from websockets.server import WebSocketServerProtocol

# Import Tascade AI components
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.core.task_manager import TaskManager
from src.core.task_timetracking import TaskTimeTrackingSystem


class TascadeMCPServer:
    """MCP server for Tascade AI."""
    
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 8765,
                 task_manager: Optional[TaskManager] = None,
                 time_tracking: Optional[TaskTimeTrackingSystem] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the MCP server.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
            task_manager: Task manager instance
            time_tracking: Time tracking system instance
            logger: Optional logger
        """
        self.host = host
        self.port = port
        self.task_manager = task_manager or TaskManager()
        self.time_tracking = time_tracking or TaskTimeTrackingSystem()
        self.logger = logger or logging.getLogger("tascade.mcp.server")
        
        # Set up command handlers
        self.command_handlers = {
            # Task management commands
            "get-tasks": self._handle_get_tasks,
            "get-task": self._handle_get_task,
            "add-task": self._handle_add_task,
            "update-task": self._handle_update_task,
            "delete-task": self._handle_delete_task,
            "set-task-status": self._handle_set_task_status,
            "get-task-dependencies": self._handle_get_task_dependencies,
            "add-task-dependency": self._handle_add_task_dependency,
            "remove-task-dependency": self._handle_remove_task_dependency,
            
            # Time tracking commands
            "get-time-entries": self._handle_get_time_entries,
            "add-time-entry": self._handle_add_time_entry,
            "update-time-entry": self._handle_update_time_entry,
            "delete-time-entry": self._handle_delete_time_entry,
            "start-tracking": self._handle_start_tracking,
            "pause-tracking": self._handle_pause_tracking,
            "resume-tracking": self._handle_resume_tracking,
            "stop-tracking": self._handle_stop_tracking,
            "get-tracking-status": self._handle_get_tracking_status,
            
            # Visualization commands
            "generate-visualization": self._handle_generate_visualization,
            "generate-dashboard": self._handle_generate_dashboard,
            
            # Server info commands
            "get-server-info": self._handle_get_server_info,
        }
    
    async def start(self):
        """Start the MCP server."""
        self.logger.info(f"Starting Tascade MCP server on {self.host}:{self.port}")
        
        async with websockets.serve(self._handle_connection, self.host, self.port):
            await asyncio.Future()  # Run forever
    
    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """
        Handle a WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            path: Connection path
        """
        client_id = str(uuid.uuid4())
        self.logger.info(f"Client connected: {client_id}")
        
        try:
            async for message in websocket:
                await self._handle_message(websocket, message, client_id)
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            self.logger.error(f"Error handling connection: {e}")
    
    async def _handle_message(self, websocket: WebSocketServerProtocol, message: str, client_id: str):
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
            
            self.logger.debug(f"Received command: {command} (ID: {request_id})")
            
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
            self.logger.error(f"Error handling message: {e}")
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
    
    async def _handle_get_tasks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get-tasks command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        status = params.get("status")
        
        # Get tasks
        tasks = self.task_manager.get_tasks(status=status)
        
        return {
            "tasks": tasks
        }
    
    async def _handle_get_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
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
        task = self.task_manager.get_task(task_id)
        
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        return {
            "task": task
        }
    
    async def _handle_add_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
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
        
        # Add task
        task_id = self.task_manager.add_task(
            title=title,
            description=description,
            priority=priority,
            status=status
        )
        
        return {
            "id": task_id
        }
    
    async def _handle_update_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle update-task command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        task_id = params.get("id")
        title = params.get("title")
        description = params.get("description")
        priority = params.get("priority")
        
        if not task_id:
            raise ValueError("Task ID is required")
        
        # Update task
        success = self.task_manager.update_task(
            task_id=task_id,
            title=title,
            description=description,
            priority=priority
        )
        
        return {
            "success": success
        }
    
    async def _handle_delete_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
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
        
        # Delete task
        success = self.task_manager.delete_task(task_id)
        
        return {
            "success": success
        }
    
    async def _handle_set_task_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle set-task-status command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        task_id = params.get("id")
        status = params.get("status")
        
        if not task_id:
            raise ValueError("Task ID is required")
        
        if not status:
            raise ValueError("Status is required")
        
        # Set task status
        success = self.task_manager.set_task_status(task_id, status)
        
        return {
            "success": success
        }
    
    async def _handle_get_task_dependencies(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get-task-dependencies command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        task_id = params.get("id")
        
        if not task_id:
            raise ValueError("Task ID is required")
        
        # Get dependencies
        dependencies = self.task_manager.get_dependencies(task_id)
        
        return {
            "dependencies": dependencies
        }
    
    async def _handle_add_task_dependency(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle add-task-dependency command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        task_id = params.get("id")
        depends_on = params.get("depends_on")
        
        if not task_id:
            raise ValueError("Task ID is required")
        
        if not depends_on:
            raise ValueError("Dependency task ID is required")
        
        # Add dependency
        success = self.task_manager.add_dependency(task_id, depends_on)
        
        return {
            "success": success
        }
    
    async def _handle_remove_task_dependency(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle remove-task-dependency command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        task_id = params.get("id")
        depends_on = params.get("depends_on")
        
        if not task_id:
            raise ValueError("Task ID is required")
        
        if not depends_on:
            raise ValueError("Dependency task ID is required")
        
        # Remove dependency
        success = self.task_manager.remove_dependency(task_id, depends_on)
        
        return {
            "success": success
        }
    
    # Time tracking command handlers
    
    async def _handle_get_time_entries(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get-time-entries command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        task_id = params.get("task_id")
        user_id = params.get("user_id")
        
        # Build filters
        filters = {}
        
        if task_id:
            filters["task_id"] = task_id
        
        if user_id:
            filters["user_id"] = user_id
        
        # Get time entries
        entries = self.time_tracking.get_time_entries(filters)
        
        # Convert to dict
        entry_dicts = [entry.to_dict() for entry in entries]
        
        return {
            "entries": entry_dicts
        }
    
    async def _handle_add_time_entry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle add-time-entry command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Create time entry
        result = self.time_tracking.create_time_entry(**params)
        
        return result
    
    async def _handle_update_time_entry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle update-time-entry command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        entry_id = params.pop("id", None)
        
        if not entry_id:
            raise ValueError("Entry ID is required")
        
        # Update time entry
        success = self.time_tracking.entry_manager.update_entry(entry_id, **params)
        
        return {
            "success": success
        }
    
    async def _handle_delete_time_entry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle delete-time-entry command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        entry_id = params.get("id")
        
        if not entry_id:
            raise ValueError("Entry ID is required")
        
        # Delete time entry
        success = self.time_tracking.entry_manager.delete_entry(entry_id)
        
        return {
            "success": success
        }
    
    async def _handle_start_tracking(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle start-tracking command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Start tracking
        session_id = self.time_tracking.start_tracking(**params)
        
        if not session_id:
            raise ValueError("Failed to start tracking")
        
        # Get session data
        session_data = self.time_tracking.get_session(session_id)
        
        return {
            "session_id": session_id,
            "session": session_data
        }
    
    async def _handle_pause_tracking(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle pause-tracking command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        session_id = params.get("session_id")
        
        if not session_id:
            raise ValueError("Session ID is required")
        
        # Pause tracking
        result = self.time_tracking.pause_tracking(session_id=session_id)
        
        if not result:
            raise ValueError("Failed to pause tracking")
        
        return result
    
    async def _handle_resume_tracking(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle resume-tracking command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        session_id = params.get("session_id")
        
        if not session_id:
            raise ValueError("Session ID is required")
        
        # Resume tracking
        result = self.time_tracking.resume_tracking(session_id=session_id)
        
        if not result:
            raise ValueError("Failed to resume tracking")
        
        return result
    
    async def _handle_stop_tracking(self, params: Dict[str, Any]) -> Dict[str, Any]:
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
        
        # Stop tracking
        result = self.time_tracking.stop_tracking(session_id=session_id)
        
        if not result:
            raise ValueError("Failed to stop tracking")
        
        return result
    
    async def _handle_get_tracking_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get-tracking-status command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        user_id = params.get("user_id")
        
        # Get tracking status
        status = self.time_tracking.get_tracking_status(user_id=user_id)
        
        return status
    
    # Visualization command handlers
    
    async def _handle_generate_visualization(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle generate-visualization command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        viz_type = params.get("type")
        data = params.get("data")
        options = params.get("options", {})
        
        if not viz_type:
            raise ValueError("Visualization type is required")
        
        if not data:
            raise ValueError("Data is required")
        
        # Import visualization module
        from src.visualization.time_charts import (
            TimeSeriesChart, GanttChart, CalendarHeatmap, ActivityHeatmap
        )
        from src.visualization.productivity_charts import (
            ProductivityTrendChart, ProductivityComparisonChart
        )
        from src.visualization.task_charts import (
            TaskCompletionChart, TaskDistributionChart, TaskRelationshipChart
        )
        
        # Create visualization
        if viz_type == "time_series":
            viz = TimeSeriesChart(data=data, **options)
        elif viz_type == "gantt":
            viz = GanttChart(data=data, **options)
        elif viz_type == "calendar":
            viz = CalendarHeatmap(data=data, **options)
        elif viz_type == "activity":
            viz = ActivityHeatmap(data=data, **options)
        elif viz_type == "productivity_trend":
            viz = ProductivityTrendChart(data=data, **options)
        elif viz_type == "productivity_comparison":
            viz = ProductivityComparisonChart(data=data, **options)
        elif viz_type == "task_completion":
            viz = TaskCompletionChart(data=data, **options)
        elif viz_type == "task_distribution":
            viz = TaskDistributionChart(data=data, **options)
        elif viz_type == "task_relationship":
            viz = TaskRelationshipChart(data=data, **options)
        else:
            raise ValueError(f"Unknown visualization type: {viz_type}")
        
        # Render visualization
        viz.render()
        
        # Get base64 image
        image_data = viz.to_base64()
        
        # Close visualization
        viz.close()
        
        return {
            "image": image_data
        }
    
    async def _handle_generate_dashboard(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle generate-dashboard command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        # Extract parameters
        title = params.get("title", "Tascade AI Dashboard")
        layout = params.get("layout", "grid")
        theme = params.get("theme", "light")
        panels = params.get("panels", [])
        
        if not panels:
            raise ValueError("Dashboard panels are required")
        
        # Import dashboard module
        from src.visualization.dashboard import Dashboard
        
        # Create dashboard
        dashboard = Dashboard(
            title=title,
            layout=layout,
            theme=theme
        )
        
        # Add panels
        for panel in panels:
            panel_type = panel.get("type")
            panel_title = panel.get("title")
            panel_data = panel.get("data")
            panel_options = panel.get("options", {})
            
            if panel_type == "time_series":
                dashboard.add_time_series(
                    title=panel_title,
                    data=panel_data,
                    **panel_options
                )
            elif panel_type == "gantt":
                dashboard.add_gantt_chart(
                    title=panel_title,
                    data=panel_data,
                    **panel_options
                )
            elif panel_type == "calendar":
                dashboard.add_calendar_heatmap(
                    title=panel_title,
                    data=panel_data,
                    **panel_options
                )
            elif panel_type == "activity":
                dashboard.add_activity_heatmap(
                    title=panel_title,
                    data=panel_data,
                    **panel_options
                )
            elif panel_type == "productivity_trend":
                dashboard.add_productivity_trend(
                    title=panel_title,
                    data=panel_data,
                    **panel_options
                )
            elif panel_type == "productivity_comparison":
                dashboard.add_productivity_comparison(
                    title=panel_title,
                    data=panel_data,
                    **panel_options
                )
            elif panel_type == "task_completion":
                dashboard.add_task_completion(
                    title=panel_title,
                    data=panel_data,
                    **panel_options
                )
            elif panel_type == "task_distribution":
                dashboard.add_task_distribution(
                    title=panel_title,
                    data=panel_data,
                    **panel_options
                )
            elif panel_type == "task_relationship":
                dashboard.add_task_relationship(
                    title=panel_title,
                    data=panel_data,
                    **panel_options
                )
        
        # Render dashboard
        html = dashboard.render()
        
        return {
            "html": html
        }
    
    # Server info command handlers
    
    async def _handle_get_server_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get-server-info command.
        
        Args:
            params: Command parameters
        
        Returns:
            Command result
        """
        return {
            "name": "Tascade AI MCP Server",
            "version": "1.0.0",
            "commands": list(self.command_handlers.keys())
        }


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up logging."""
    # Convert string log level to numeric value
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Create logger for this module
    logger = logging.getLogger("tascade.mcp.server")
    
    return logger


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Tascade AI MCP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind to")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Log level")
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging(args.log_level)
    
    # Create server
    server = TascadeMCPServer(
        host=args.host,
        port=args.port,
        logger=logger
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
