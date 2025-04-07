"""
AI Agent Example

This example demonstrates how to build an AI agent that uses the MCP server
to interact with your system and perform tasks autonomously.
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Any, Optional
from mcp_client import MCPClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("ai_agent.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ai_agent")

class AIAgent:
    """
    An autonomous AI agent that uses the MCP server to interact with the system
    and perform tasks based on high-level goals.
    """
    
    def __init__(self, server_url: str, api_key: str, model_id: str):
        """
        Initialize the AI agent.
        
        Args:
            server_url: URL of the MCP server
            api_key: API key for authentication
            model_id: ID of the AI model to use for reasoning
        """
        self.client = MCPClient(server_url, api_key)
        self.model_id = model_id
        self.working_dir = os.getcwd()
        self.tasks = []
        
    def connect(self) -> bool:
        """
        Connect to the MCP server and the AI model.
        
        Returns:
            True if connection was successful, False otherwise
        """
        # Check if model is already connected
        result = self.client.list_models()
        
        if not result.get("success", False):
            logger.error(f"Failed to list models: {result.get('error')}")
            return False
        
        models = result.get("models", [])
        
        if any(model["model_id"] == self.model_id for model in models):
            logger.info(f"Model {self.model_id} is already connected")
            return True
        
        # Connect to the model
        result = self.client.connect_model(
            self.model_id,
            "ollama",
            {"host": "http://localhost:11434"}
        )
        
        if not result.get("success", False):
            logger.error(f"Failed to connect to model {self.model_id}: {result.get('error')}")
            return False
        
        logger.info(f"Successfully connected to model {self.model_id}")
        return True
    
    def query_model(self, prompt: str) -> str:
        """
        Query the AI model for reasoning.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            The model's response as a string
        """
        result = self.client.query_model(self.model_id, self.model_id, prompt)
        
        if not result.get("success", False):
            logger.error(f"Failed to query model: {result.get('error')}")
            return ""
        
        return result.get("response", "")
    
    def execute_command(self, command: str, args: List[str] = None) -> Dict:
        """
        Execute a system command.
        
        Args:
            command: The command to execute
            args: Command arguments
            
        Returns:
            Command execution result
        """
        return self.client.execute_system_command(
            self.model_id,
            command,
            args,
            self.working_dir
        )
    
    def read_file(self, path: str) -> str:
        """
        Read a file.
        
        Args:
            path: Path to the file
            
        Returns:
            File content or empty string if failed
        """
        result = self.client.read_file(self.model_id, path)
        
        if not result.get("success", False):
            logger.error(f"Failed to read file {path}: {result.get('error')}")
            return ""
        
        return result.get("content", "")
    
    def write_file(self, path: str, content: str) -> bool:
        """
        Write to a file.
        
        Args:
            path: Path to the file
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        result = self.client.write_file(self.model_id, path, content)
        
        if not result.get("success", False):
            logger.error(f"Failed to write to file {path}: {result.get('error')}")
            return False
        
        return True
    
    def start_program(self, program_path: str, args: List[str] = None) -> Optional[int]:
        """
        Start a program.
        
        Args:
            program_path: Path to the program
            args: Program arguments
            
        Returns:
            Process ID if successful, None otherwise
        """
        result = self.client.start_program(self.model_id, program_path, args)
        
        if not result.get("success", False):
            logger.error(f"Failed to start program {program_path}: {result.get('error')}")
            return None
        
        return result.get("pid")
    
    def stop_program(self, pid: int) -> bool:
        """
        Stop a program.
        
        Args:
            pid: Process ID
            
        Returns:
            True if successful, False otherwise
        """
        result = self.client.stop_program(self.model_id, pid)
        
        if not result.get("success", False):
            logger.error(f"Failed to stop program with PID {pid}: {result.get('error')}")
            return False
        
        return True
    
    def analyze_system_state(self) -> Dict:
        """
        Analyze the current system state.
        
        Returns:
            Dictionary with system state information
        """
        system_state = {}
        
        # Get current directory files
        list_result = self.client.list_directory(self.model_id, self.working_dir)
        if list_result.get("success", False):
            system_state["files"] = list_result.get("files", [])
        
        # Get running processes
        ps_result = self.execute_command("ps", ["-ef"])
        if ps_result.get("success", False):
            system_state["processes"] = ps_result.get("stdout", "")
        
        # Get system info
        if sys.platform == "win32":
            sys_info_result = self.execute_command("systeminfo")
        else:
            sys_info_result = self.execute_command("uname", ["-a"])
        
        if sys_info_result.get("success", False):
            system_state["system_info"] = sys_info_result.get("stdout", "")
        
        return system_state
    
    def plan_tasks(self, goal: str) -> List[Dict]:
        """
        Plan tasks to achieve a high-level goal.
        
        Args:
            goal: High-level goal
            
        Returns:
            List of planned tasks
        """
        # Analyze system state
        system_state = self.analyze_system_state()
        
        # Create prompt for the AI model
        prompt = f"""
        GOAL: {goal}
        
        CURRENT SYSTEM STATE:
        
        Files in current directory:
        {system_state.get('files', [])}
        
        System information:
        {system_state.get('system_info', '')}
        
        Based on the goal and current system state, create a detailed plan with specific steps to achieve the goal.
        Each step should be one of the following types: command, file_operation, or program_control.
        
        Return the plan as a JSON array of tasks, where each task has the following structure:
        {{
            "type": "command | file_operation | program_control",
            "description": "Description of the task",
            "params": {{
                // Parameters specific to the task type
            }}
        }}
        
        ONLY RETURN THE JSON ARRAY WITHOUT ANY ADDITIONAL TEXT OR EXPLANATION.
        """
        
        # Query the AI model for planning
        response = self.query_model(prompt)
        
        # Parse the response as JSON
        try:
            # Find JSON in the response (it might be surrounded by text)
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                tasks = json.loads(json_text)
                return tasks
            else:
                logger.error("Failed to find JSON array in model response")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from model response: {str(e)}")
            return []
    
    def execute_tasks(self, tasks: List[Dict]) -> bool:
        """
        Execute a list of planned tasks.
        
        Args:
            tasks: List of tasks to execute
            
        Returns:
            True if all tasks were successful, False otherwise
        """
        self.tasks = tasks
        all_successful = True
        
        for i, task in enumerate(tasks):
            task_type = task.get("type")
            description = task.get("description", "")
            params = task.get("params", {})
            
            logger.info(f"Executing task {i+1}/{len(tasks)}: {description}")
            
            success = False
            
            if task_type == "command":
                command = params.get("command", "")
                args = params.get("args", [])
                
                result = self.execute_command(command, args)
                success = result.get("success", False)
                
                # Log command output
                if success:
                    logger.info(f"Command output: {result.get('stdout', '')}")
                else:
                    logger.error(f"Command error: {result.get('stderr', '')}")
            
            elif task_type == "file_operation":
                operation = params.get("operation", "")
                path = params.get("path", "")
                content = params.get("content", "")
                
                if operation == "read":
                    content = self.read_file(path)
                    success = content != ""
                elif operation == "write":
                    success = self.write_file(path, content)
                elif operation == "delete":
                    result = self.client.delete_file(self.model_id, path)
                    success = result.get("success", False)
                else:
                    logger.error(f"Unknown file operation: {operation}")
            
            elif task_type == "program_control":
                action = params.get("action", "")
                
                if action == "start":
                    program_path = params.get("program_path", "")
                    args = params.get("args", [])
                    
                    pid = self.start_program(program_path, args)
                    success = pid is not None
                    
                    # Store PID for later use
                    if success:
                        params["pid"] = pid
                
                elif action == "stop":
                    pid = params.get("pid")
                    success = self.stop_program(pid)
                
                else:
                    logger.error(f"Unknown program action: {action}")
            
            else:
                logger.error(f"Unknown task type: {task_type}")
            
            # Update task status
            task["success"] = success
            
            if not success:
                logger.error(f"Task failed: {description}")
                all_successful = False
        
        return all_successful
    
    def achieve_goal(self, goal: str) -> bool:
        """
        Achieve a high-level goal.
        
        Args:
            goal: High-level goal
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Attempting to achieve goal: {goal}")
        
        # Plan tasks
        tasks = self.plan_tasks(goal)
        
        if not tasks:
            logger.error("Failed to plan tasks")
            return False
        
        logger.info(f"Planned {len(tasks)} tasks")
        
        # Execute tasks
        return self.execute_tasks(tasks)

# Example usage
if __name__ == "__main__":
    # Configuration
    SERVER_URL = "http://localhost:8000"
    API_KEY = "your-secret-api-key"
    MODEL_ID = "llama2"  # Change to your preferred model
    
    # Create agent
    agent = AIAgent(SERVER_URL, API_KEY, MODEL_ID)
    
    # Connect to MCP server and AI model
    if not agent.connect():
        logger.error("Failed to connect to MCP server or AI model")
        sys.exit(1)
    
    # Define a goal
    goal = "Create a simple web server that serves a 'Hello, World!' page"
    
    # Achieve the goal
    success = agent.achieve_goal(goal)
    
    if success:
        logger.info(f"Successfully achieved goal: {goal}")
    else:
        logger.error(f"Failed to achieve goal: {goal}")
