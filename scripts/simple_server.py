#!/usr/bin/env python3

"""
Simple MCP Server for Tascade AI

This script implements a simple MCP server for Tascade AI that handles
commands from the Windsurf IDE.
"""

import json
import os
import sys
import asyncio
import websockets
import subprocess
import argparse
from datetime import datetime

# Parse command line arguments
parser = argparse.ArgumentParser(description='Simple MCP Server for Tascade AI')
parser.add_argument('--port', type=int, default=8765, help='Port to run the server on')
args = parser.parse_args()

# Store connected clients
connected = set()

# Command handlers
async def handle_generate_tasks(params):
    """
    Handle the generate-tasks command
    
    This command generates tasks from a PRD file using AI.
    
    Args:
        params (dict): Command parameters
            - input_file (str): Path to the PRD file
            - output_file (str): Path to save the generated tasks
            - num_tasks (int, optional): Number of tasks to generate
            - provider (str, optional): AI provider to use (anthropic, openai, perplexity)
            - priority (str, optional): Default priority for generated tasks
            
    Returns:
        dict: Command result
    """
    try:
        # Validate parameters
        if 'input_file' not in params:
            return {'error': 'Missing required parameter: input_file'}
        
        if 'output_file' not in params:
            return {'error': 'Missing required parameter: output_file'}
        
        # Build the command
        cmd = ['node', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bin', 'tascade-ai.js'), 
               'generate', 
               '--input', params['input_file'], 
               '--output', params['output_file']]
        
        # Add optional parameters
        if 'num_tasks' in params:
            cmd.extend(['--num-tasks', str(params['num_tasks'])])
        
        if 'provider' in params:
            cmd.extend(['--provider', params['provider']])
        
        if 'priority' in params:
            cmd.extend(['--priority', params['priority']])
        
        if params.get('force', False):
            cmd.append('--force')
        
        # Run the command
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            return {'error': f'Failed to generate tasks: {stderr}'}
        
        # Parse the output file
        try:
            with open(params['output_file'], 'r') as f:
                tasks = json.load(f)
            
            return {
                'success': True,
                'tasks': tasks['tasks'],
                'metadata': tasks.get('metadata', {}),
                'message': 'Tasks generated successfully'
            }
        except Exception as e:
            return {'error': f'Failed to read generated tasks: {str(e)}'}
    
    except Exception as e:
        return {'error': f'Error generating tasks: {str(e)}'}

# Command router
async def handle_command(command, params):
    """
    Route commands to the appropriate handler
    
    Args:
        command (str): Command name
        params (dict): Command parameters
        
    Returns:
        dict: Command result
    """
    if command == 'generate-tasks':
        return await handle_generate_tasks(params)
    else:
        return {'error': f'Unknown command: {command}'}

# Message handler
async def handle_message(websocket, message):
    """
    Handle a message from a client
    
    Args:
        websocket (WebSocketServerProtocol): WebSocket connection
        message (str): Message from the client
    """
    try:
        data = json.loads(message)
        
        if 'command' not in data:
            await websocket.send(json.dumps({'error': 'Missing command'}))
            return
        
        command = data['command']
        params = data.get('params', {})
        
        # Handle the command
        result = await handle_command(command, params)
        
        # Add command and timestamp to the result
        result['command'] = command
        result['timestamp'] = datetime.now().isoformat()
        
        # Send the result back to the client
        await websocket.send(json.dumps(result))
    
    except json.JSONDecodeError:
        await websocket.send(json.dumps({'error': 'Invalid JSON'}))
    except Exception as e:
        await websocket.send(json.dumps({'error': f'Error handling message: {str(e)}'}))

# WebSocket handler
async def handler(websocket, path):
    """
    Handle a WebSocket connection
    
    Args:
        websocket (WebSocketServerProtocol): WebSocket connection
        path (str): Connection path
    """
    # Register the client
    connected.add(websocket)
    
    try:
        # Send a welcome message
        await websocket.send(json.dumps({
            'message': 'Welcome to Tascade AI MCP Server',
            'timestamp': datetime.now().isoformat()
        }))
        
        # Handle messages
        async for message in websocket:
            await handle_message(websocket, message)
    
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # Unregister the client
        connected.remove(websocket)

# Start the server
async def main():
    """Start the WebSocket server"""
    port = args.port
    
    # Start the server
    async with websockets.serve(handler, "localhost", port):
        print(f"Tascade AI MCP Server running at ws://localhost:{port}")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTascade AI MCP Server stopped")
        sys.exit(0)
