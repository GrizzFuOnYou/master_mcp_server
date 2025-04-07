"""
AI MCP Client Library

This library allows AI models to connect to the MCP server
and perform various system operations.
"""

import os
import sys
import json
import time
import requests
from typing import Dict, List, Any, Optional, Union

class MCPClient:
    """Client for interacting with the AI MCP Server"""
    
    def __init__(self, server_url: str, api_key: str):
        """
        Initialize the MCP client
        
        Args:
            server_url: URL of the MCP server (e.g., http://localhost:8000)
            api_key: API key for authentication
        """
        self.server_url = server_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make an HTTP request to the MCP server"""
        url = f"{self.server_url}/{endpoint}"
        
        try:
            if method.lower() == "get":
                response = requests.get(url, headers=self.headers)
            elif method.lower() == "post":
                response = requests.post(url, headers=self.headers, json=data)
            else:
                return {"success": False, "error": f"Unsupported HTTP method: {method}"}
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Request error: {str(e)}"}
            
    def connect_model(self, model_id: str, model_type: str, config: Dict = None) -> Dict:
        """
        Connect to an AI model
        
        Args:
            model_id: ID of the model (e.g., llama2)
            model_type: Type of model (e.g., ollama)
            config: Configuration for the model
            
        Returns:
            Dict with connection result
        """
        if config is None:
            config = {}
            
        data = {
            "model_id": model_id,
            "model_type": model_type,
            "config": config
        }
        
        return self._make_request("post", "connect_model", data)
        
    def disconnect_model(self, model_id: str) -> Dict:
        """
        Disconnect from an AI model
        
        Args:
            model_id: ID of the model
            
        Returns:
            Dict with disconnection result
        """
        return self._make_request("post", f"disconnect_model/{model_id}")
        
    def list_models(self) -> Dict:
        """
        List all connected models
        
        Returns:
            Dict with list of connected models
        """
        return self._make_request("get", "list_models")
        
    def execute_system_command(self, model_id: str, command: str, args: List[str] = None, 
                               working_dir: str = None, timeout: int = 60) -> Dict:
        """
        Execute a system command
        
        Args:
            model_id: ID of the requesting model
            command: Command to execute
            args: Command arguments
            working_dir: Working directory
            timeout: Command timeout in seconds
            
        Returns:
            Dict with command execution result
        """
        if args is None:
            args = []
            
        data = {
            "model_id": model_id,
            "task_type": "system_command",
            "data": {
                "command": command,
                "args": args,
                "working_dir": working_dir,
                "timeout": timeout
            }
        }
        
        response = self._make_request("post", "execute_task", data)
        
        if not response.get("success", False):
            return response
            
        # Wait for task completion
        task_id = response.get("task_id")
        
        while True:
            status = self._make_request("get", f"task_status/{task_id}")
            
            if status.get("status") in ["completed", "failed"]:
                return status.get("result", {"success": False, "error": status.get("error")})
                
            time.sleep(0.5)
            
    def execute_file_operation(self, model_id: str, operation: str, path: str, 
                               content: str = None) -> Dict:
        """
        Execute a file operation
        
        Args:
            model_id: ID of the requesting model
            operation: Operation type (read, write, delete, list)
            path: File or directory path
            content: File content (for write operation)
            
        Returns:
            Dict with file operation result
        """
        data = {
            "model_id": model_id,
            "task_type": "file_operation",
            "data": {
                "operation": operation,
                "path": path,
                "content": content
            }
        }
        
        response = self._make_request("post", "execute_task", data)
        
        if not response.get("success", False):
            return response
            
        # Wait for task completion
        task_id = response.get("task_id")
        
        while True:
            status = self._make_request("get", f"task_status/{task_id}")
            
            if status.get("status") in ["completed", "failed"]:
                return status.get("result", {"success": False, "error": status.get("error")})
                
            time.sleep(0.5)
            
    def control_program(self, model_id: str, action: str, program_path: str = None, 
                       args: List[str] = None, pid: int = None) -> Dict:
        """
        Control a program
        
        Args:
            model_id: ID of the requesting model
            action: Action type (start, stop)
            program_path: Path to the program (for start action)
            args: Program arguments (for start action)
            pid: Process ID (for stop action)
            
        Returns:
            Dict with program control result
        """
        if args is None:
            args = []
            
        data = {
            "model_id": model_id,
            "task_type": "program_control",
            "data": {
                "action": action
            }
        }
        
        if action == "start":
            data["data"]["program_path"] = program_path
            data["data"]["args"] = args
        elif action == "stop":
            data["data"]["pid"] = pid
            
        response = self._make_request("post", "execute_task", data)
        
        if not response.get("success", False):
            return response
            
        # Wait for task completion
        task_id = response.get("task_id")
        
        while True:
            status = self._make_request("get", f"task_status/{task_id}")
            
            if status.get("status") in ["completed", "failed"]:
                return status.get("result", {"success": False, "error": status.get("error")})
                
            time.sleep(0.5)
            
    def query_model(self, model_id: str, target_model: str, prompt: str) -> Dict:
        """
        Query an AI model
        
        Args:
            model_id: ID of the requesting model
            target_model: ID of the model to query
            prompt: Prompt to send to the model
            
        Returns:
            Dict with model query result
        """
        data = {
            "model_id": model_id,
            "task_type": "model_query",
            "data": {
                "target_model": target_model,
                "prompt": prompt
            }
        }
        
        response = self._make_request("post", "execute_task", data)
        
        if not response.get("success", False):
            return response
            
        # Wait for task completion
        task_id = response.get("task_id")
        
        while True:
            status = self._make_request("get", f"task_status/{task_id}")
            
            if status.get("status") in ["completed", "failed"]:
                return status.get("result", {"success": False, "error": status.get("error")})
                
            time.sleep(0.5)
            
    # Convenience methods for file operations
    
    def read_file(self, model_id: str, path: str) -> Dict:
        """Read a file"""
        return self.execute_file_operation(model_id, "read", path)
        
    def write_file(self, model_id: str, path: str, content: str) -> Dict:
        """Write to a file"""
        return self.execute_file_operation(model_id, "write", path, content)
        
    def delete_file(self, model_id: str, path: str) -> Dict:
        """Delete a file or directory"""
        return self.execute_file_operation(model_id, "delete", path)
        
    def list_directory(self, model_id: str, path: str) -> Dict:
        """List directory contents"""
        return self.execute_file_operation(model_id, "list", path)
        
    # Convenience methods for program control
    
    def start_program(self, model_id: str, program_path: str, args: List[str] = None) -> Dict:
        """Start a program"""
        return self.control_program(model_id, "start", program_path, args)
        
    def stop_program(self, model_id: str, pid: int) -> Dict:
        """Stop a program"""
        return self.control_program(model_id, "stop", pid=pid)

# Example usage
if __name__ == "__main__":
    # Initialize client
    client = MCPClient("http://localhost:8000", "your-secret-api-key")
    
    # Connect to an Ollama model
    result = client.connect_model("llama2", "ollama", {"host": "http://localhost:11434"})
    print(f"Connection result: {result}")
    
    # Execute a command
    result = client.execute_system_command("llama2", "echo", ["Hello, World!"])
    print(f"Command result: {result}")
    
    # Write a file
    result = client.write_file("llama2", "test.txt", "This is a test file created by an AI!")
    print(f"File write result: {result}")
    
    # Read the file
    result = client.read_file("llama2", "test.txt")
    print(f"File content: {result.get('content')}")
    
    # List directory
    result = client.list_directory("llama2", ".")
    print(f"Directory contents: {result.get('files')}")
    
    # Start a program
    result = client.start_program("llama2", "notepad.exe")
    print(f"Program start result: {result}")
    
    # Get program PID
    pid = result.get("pid")
    
    # Wait a few seconds
    print("Waiting 5 seconds...")
    time.sleep(5)
    
    # Stop the program
    result = client.stop_program("llama2", pid)
    print(f"Program stop result: {result}")
    
    # Query the model
    result = client.query_model("llama2", "llama2", "What is the capital of France?")
    print(f"Model response: {result.get('response')}")
    
    # Disconnect from the model
    result = client.disconnect_model("llama2")
    print(f"Disconnection result: {result}")
