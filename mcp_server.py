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