#!/usr/bin/env python3
"""
Test script for Tascade AI MCP integration with Windsurf.

This script tests all the MCP commands that Windsurf will use to interact with
Tascade AI. It verifies that the MCP server is properly configured and working.
"""

import asyncio
import json
import sys
import os
import uuid
import websockets
from datetime import datetime
import argparse

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TascadeWindsurfTester:
    """Test the Tascade AI MCP integration with Windsurf."""
    
    def __init__(self, host="localhost", port=8766):
        """
        Initialize the tester.
        
        Args:
            host: The host where the MCP server is running
            port: The port where the MCP server is running
        """
        self.url = f"ws://{host}:{port}"
        self.websocket = None
        self.test_results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "details": []
        }
    
    async def connect(self):
        """Connect to the MCP server."""
        try:
            self.websocket = await websockets.connect(self.url)
            print(f"✅ Connected to {self.url}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to {self.url}: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.websocket:
            await self.websocket.close()
            print("Disconnected from server")
    
    async def send_command(self, command, params=None):
        """
        Send a command to the MCP server.
        
        Args:
            command: The command to send
            params: The parameters for the command
        
        Returns:
            The response from the server
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
        
        # Receive response
        response = await self.websocket.recv()
        return json.loads(response)
    
    async def run_test(self, name, command, params=None, validation_func=None):
        """
        Run a test for a specific command.
        
        Args:
            name: The name of the test
            command: The command to test
            params: The parameters for the command
            validation_func: A function to validate the response
        
        Returns:
            True if the test passed, False otherwise
        """
        self.test_results["total"] += 1
        
        try:
            print(f"\n🔍 Testing: {name}")
            print(f"  Command: {command}")
            print(f"  Params: {json.dumps(params or {})}")
            
            response = await self.send_command(command, params)
            
            if response.get("error"):
                error = response["error"]
                print(f"❌ Error: {error.get('message')} (Code: {error.get('code')})")
                self.test_results["failed"] += 1
                self.test_results["details"].append({
                    "name": name,
                    "command": command,
                    "params": params,
                    "status": "failed",
                    "error": error
                })
                return False
            
            result = response.get("result")
            
            if validation_func and not validation_func(result):
                print(f"❌ Validation failed for {name}")
                self.test_results["failed"] += 1
                self.test_results["details"].append({
                    "name": name,
                    "command": command,
                    "params": params,
                    "status": "failed",
                    "error": "Validation failed",
                    "result": result
                })
                return False
            
            print(f"✅ {name} passed")
            self.test_results["passed"] += 1
            self.test_results["details"].append({
                "name": name,
                "command": command,
                "params": params,
                "status": "passed",
                "result": result
            })
            return True
        except Exception as e:
            print(f"❌ Exception in {name}: {e}")
            self.test_results["failed"] += 1
            self.test_results["details"].append({
                "name": name,
                "command": command,
                "params": params,
                "status": "failed",
                "error": str(e)
            })
            return False
    
    def print_summary(self):
        """Print a summary of the test results."""
        print("\n" + "=" * 50)
        print(f"Test Summary: {self.test_results['passed']}/{self.test_results['total']} tests passed")
        print("=" * 50)
        
        if self.test_results["failed"] > 0:
            print("\nFailed Tests:")
            for detail in self.test_results["details"]:
                if detail["status"] == "failed":
                    print(f"- {detail['name']}: {detail.get('error', 'Unknown error')}")
        
        print("\nPassed Tests:")
        for detail in self.test_results["details"]:
            if detail["status"] == "passed":
                print(f"- {detail['name']}")
        
        print("\n" + "=" * 50)
        
        if self.test_results["failed"] == 0:
            print("🎉 All tests passed! The Tascade AI MCP server is ready for Windsurf integration.")
        else:
            print(f"⚠️  {self.test_results['failed']} tests failed. Please fix the issues before proceeding.")
    
    async def run_all_tests(self):
        """Run all tests."""
        # Test server info
        await self.run_test(
            "Get Server Info",
            "get-server-info",
            validation_func=lambda result: isinstance(result, dict) and "name" in result
        )
        
        # Test task management
        task_id = None
        
        # Add task
        add_task_result = await self.run_test(
            "Add Task",
            "add-task",
            {
                "title": "Test task for Windsurf integration",
                "description": "This task was created during Windsurf integration testing",
                "priority": "high"
            },
            validation_func=lambda result: isinstance(result, dict) and "id" in result
        )
        
        if add_task_result:
            task_id = self.test_results["details"][-1]["result"]["id"]
            
            # Get task
            await self.run_test(
                "Get Task",
                "get-task",
                {
                    "id": task_id
                },
                validation_func=lambda result: isinstance(result, dict) and "task" in result
            )
            
            # Update task
            await self.run_test(
                "Update Task",
                "update-task",
                {
                    "id": task_id,
                    "description": "Updated description during Windsurf integration testing"
                },
                validation_func=lambda result: isinstance(result, dict) and result.get("success") is True
            )
            
            # Get all tasks
            await self.run_test(
                "Get All Tasks",
                "get-tasks",
                validation_func=lambda result: isinstance(result, dict) and "tasks" in result
            )
            
            # Start time tracking
            session_id = None
            start_tracking_result = await self.run_test(
                "Start Time Tracking",
                "start-tracking",
                {
                    "task_id": task_id,
                    "description": "Working on Windsurf integration testing"
                },
                validation_func=lambda result: isinstance(result, dict) and "session_id" in result
            )
            
            if start_tracking_result:
                session_id = self.test_results["details"][-1]["result"]["session_id"]
                
                # Wait a bit to simulate work
                print("Waiting 3 seconds to simulate work...")
                await asyncio.sleep(3)
                
                # Stop time tracking
                await self.run_test(
                    "Stop Time Tracking",
                    "stop-tracking",
                    {
                        "session_id": session_id
                    },
                    validation_func=lambda result: isinstance(result, dict) and result.get("success") is True
                )
                
                # Get time entries
                await self.run_test(
                    "Get Time Entries",
                    "get-time-entries",
                    {
                        "task_id": task_id
                    },
                    validation_func=lambda result: isinstance(result, dict) and "entries" in result
                )
            
            # Delete task (cleanup)
            await self.run_test(
                "Delete Task",
                "delete-task",
                {
                    "id": task_id
                },
                validation_func=lambda result: isinstance(result, dict) and result.get("success") is True
            )
        
        # Print summary
        self.print_summary()
        
        return self.test_results["failed"] == 0


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test Tascade AI MCP integration with Windsurf")
    parser.add_argument("--host", default="localhost", help="Host where the MCP server is running")
    parser.add_argument("--port", type=int, default=8766, help="Port where the MCP server is running")
    
    args = parser.parse_args()
    
    tester = TascadeWindsurfTester(args.host, args.port)
    
    try:
        if await tester.connect():
            success = await tester.run_all_tests()
            
            if success:
                print("\n✅ Tascade AI MCP server is ready for npm publishing!")
            else:
                print("\n❌ Please fix the issues before npm publishing.")
                sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await tester.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
