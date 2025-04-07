"""
AI Master Control Program (MCP) Server

This server allows AI models to connect with your computer system,
enabling file operations, program control, and various system tasks.
"""

import os
import sys
import json
import subprocess
import logging
import signal
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

# --- Models ---

class SystemCommand(BaseModel):
    """Model for executing system commands"""
    command: str
    args: List[str] = []
    working_dir: Optional[str] = None
    timeout: Optional[int] = 60

class FileOperation(BaseModel):
    """Model for file operations"""
    operation: str  # read, write, delete, list
    path: str
    content: Optional[str] = None
    
class TaskRequest(BaseModel):
    """Model for AI task requests"""
    model_id: str
    task_type: str  # system_command, file_operation, program_control
    data: Dict[str, Any]
    
class TaskResponse(BaseModel):
    """Model for task responses"""
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None

class ModelConnectRequest(BaseModel):
    """Model for AI model connection requests"""
    model_id: str
    model_type: str  # ollama, openai, etc.
    config: Dict[str, Any] = {}

# --- Core Server ---

app = FastAPI(title="AI Master Control Program")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security setup - use environment variable in production
API_KEY = "your-secret-api-key"  # Replace with secure key management
security = HTTPBearer()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("mcp_server.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("mcp_server")

# Task tracking
tasks = {}
connected_models = {}
running_processes = {}

# --- Authentication & Security ---

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# --- File Operations ---

def execute_file_operation(operation: FileOperation) -> Dict[str, Any]:
    path = Path(operation.path)
    
    try:
        if operation.operation == "read":
            if not path.exists():
                return {"success": False, "error": "File not found"}
            with open(path, "r") as f:
                content = f.read()
            return {"success": True, "content": content}
            
        elif operation.operation == "write":
            if operation.content is None:
                return {"success": False, "error": "No content provided"}
            
            # Create directories if they don't exist
            if not path.parent.exists():
                path.parent.mkdir(parents=True)
                
            with open(path, "w") as f:
                f.write(operation.content)
            return {"success": True}
            
        elif operation.operation == "delete":
            if not path.exists():
                return {"success": False, "error": "File not found"}
            
            if path.is_dir():
                import shutil
                shutil.rmtree(path)
            else:
                path.unlink()
            return {"success": True}
            
        elif operation.operation == "list":
            if not path.exists() or not path.is_dir():
                return {"success": False, "error": "Directory not found"}
            
            files = [str(f.relative_to(path)) for f in path.glob("**/*")]
            return {"success": True, "files": files}
            
        else:
            return {"success": False, "error": f"Unknown operation: {operation.operation}"}
            
    except Exception as e:
        logger.error(f"File operation error: {str(e)}")
        return {"success": False, "error": str(e)}

# --- System Command Execution ---

def execute_system_command(command_request: SystemCommand) -> Dict[str, Any]:
    cmd = [command_request.command] + command_request.args
    cwd = command_request.working_dir
    timeout = command_request.timeout

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            text=True,
            shell=False  # More secure, but requires full paths
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            return {
                "success": True if process.returncode == 0 else False,
                "returncode": process.returncode,
                "stdout": stdout,
                "stderr": stderr
            }
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds"
            }
            
    except Exception as e:
        logger.error(f"Command execution error: {str(e)}")
        return {"success": False, "error": str(e)}

# --- Program Control ---

def start_program(program_path: str, args: List[str] = None) -> Dict[str, Any]:
    if args is None:
        args = []
        
    cmd = [program_path] + args
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        pid = process.pid
        running_processes[pid] = process
        
        return {
            "success": True,
            "pid": pid,
            "message": f"Program started with PID {pid}"
        }
        
    except Exception as e:
        logger.error(f"Program start error: {str(e)}")
        return {"success": False, "error": str(e)}

def stop_program(pid: int) -> Dict[str, Any]:
    if pid not in running_processes:
        return {"success": False, "error": f"No program with PID {pid} is being tracked"}
        
    process = running_processes[pid]
    
    try:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            
        del running_processes[pid]
        return {"success": True, "message": f"Program with PID {pid} stopped"}
        
    except Exception as e:
        logger.error(f"Program stop error: {str(e)}")
        return {"success": False, "error": str(e)}

# --- Ollama Integration ---

def connect_to_ollama(model_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Connect to an Ollama model"""
    import requests
    
    ollama_host = config.get("host", "http://localhost:11434")
    
    # Check if model exists
    try:
        response = requests.get(f"{ollama_host}/api/tags")
        available_models = response.json().get("models", [])
        
        model_exists = any(model["name"] == model_id for model in available_models)
        
        if not model_exists:
            return {
                "success": False,
                "error": f"Model {model_id} not found in Ollama"
            }
            
        # Register model in connected models
        connected_models[model_id] = {
            "type": "ollama",
            "config": config,
            "host": ollama_host
        }
        
        return {
            "success": True,
            "message": f"Connected to Ollama model {model_id}"
        }
        
    except Exception as e:
        logger.error(f"Ollama connection error: {str(e)}")
        return {"success": False, "error": str(e)}

def query_ollama_model(model_id: str, prompt: str) -> Dict[str, Any]:
    """Query an Ollama model"""
    import requests
    
    if model_id not in connected_models:
        return {"success": False, "error": f"Model {model_id} not connected"}
        
    model_info = connected_models[model_id]
    
    if model_info["type"] != "ollama":
        return {"success": False, "error": f"Model {model_id} is not an Ollama model"}
        
    ollama_host = model_info["host"]
    
    try:
        response = requests.post(
            f"{ollama_host}/api/generate",
            json={
                "model": model_id,
                "prompt": prompt,
                "stream": False
            }
        )
        
        result = response.json()
        return {
            "success": True,
            "response": result.get("response", ""),
            "metrics": result.get("metrics", {})
        }
        
    except Exception as e:
        logger.error(f"Ollama query error: {str(e)}")
        return {"success": False, "error": str(e)}

# --- API Endpoints ---

@app.post("/connect_model", response_model=Dict[str, Any])
async def connect_model(
    request: ModelConnectRequest,
    api_key: str = Depends(verify_api_key)
):
    """Connect to an AI model (Ollama, etc.)"""
    model_id = request.model_id
    model_type = request.model_type
    config = request.config
    
    if model_type == "ollama":
        result = connect_to_ollama(model_id, config)
    else:
        result = {
            "success": False,
            "error": f"Unsupported model type: {model_type}"
        }
        
    return result

@app.post("/execute_task", response_model=TaskResponse)
async def execute_task(
    request: TaskRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Execute a task requested by an AI model"""
    task_id = f"task_{int(time.time())}_{len(tasks) + 1}"
    model_id = request.model_id
    task_type = request.task_type
    data = request.data
    
    # Initialize task
    tasks[task_id] = {
        "status": "processing",
        "model_id": model_id,
        "task_type": task_type,
        "data": data,
        "result": None,
        "error": None
    }
    
    async def process_task():
        try:
            if task_type == "system_command":
                command = SystemCommand(**data)
                result = execute_system_command(command)
                
            elif task_type == "file_operation":
                operation = FileOperation(**data)
                result = execute_file_operation(operation)
                
            elif task_type == "program_control":
                action = data.get("action")
                
                if action == "start":
                    result = start_program(data.get("program_path"), data.get("args", []))
                elif action == "stop":
                    result = stop_program(data.get("pid"))
                else:
                    result = {"success": False, "error": f"Unknown program action: {action}"}
            
            elif task_type == "model_query":
                target_model = data.get("target_model")
                prompt = data.get("prompt")
                
                if not target_model or not prompt:
                    result = {"success": False, "error": "Missing target_model or prompt"}
                else:
                    result = query_ollama_model(target_model, prompt)
            
            else:
                result = {"success": False, "error": f"Unknown task type: {task_type}"}
                
            # Update task status
            tasks[task_id]["status"] = "completed" if result.get("success", False) else "failed"
            tasks[task_id]["result"] = result
            
        except Exception as e:
            logger.error(f"Task processing error: {str(e)}")
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = str(e)
    
    # Process task in background
    background_tasks.add_task(process_task)
    
    return TaskResponse(
        task_id=task_id,
        status="processing",
        result=None,
        error=None
    )

@app.get("/task_status/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get the status of a task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
    task = tasks[task_id]
    
    return TaskResponse(
        task_id=task_id,
        status=task["status"],
        result=task.get("result"),
        error=task.get("error")
    )

@app.get("/list_models", response_model=Dict[str, Any])
async def list_models(
    api_key: str = Depends(verify_api_key)
):
    """List all connected models"""
    return {
        "success": True,
        "models": [
            {
                "model_id": model_id,
                "type": info["type"],
                "config": info["config"]
            }
            for model_id, info in connected_models.items()
        ]
    }

@app.post("/disconnect_model/{model_id}", response_model=Dict[str, Any])
async def disconnect_model(
    model_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Disconnect from an AI model"""
    if model_id not in connected_models:
        return {"success": False, "error": f"Model {model_id} not connected"}
        
    del connected_models[model_id]
    return {"success": True, "message": f"Model {model_id} disconnected"}

# --- Main Entry Point ---

def cleanup():
    """Cleanup function to terminate all running processes"""
    for pid, process in running_processes.items():
        try:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        except Exception as e:
            logger.error(f"Error terminating process {pid}: {str(e)}")

def signal_handler(sig, frame):
    """Handle termination signals"""
    logger.info("Shutting down MCP server...")
    cleanup()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    # Setup environment - move to config in production
    host = "0.0.0.0"
    port = 8000
    
    logger.info(f"Starting AI MCP server on {host}:{port}")
    
    uvicorn.run(app, host=host, port=port)