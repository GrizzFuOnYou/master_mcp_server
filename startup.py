"""
AI MCP Server Startup Script

This script starts the AI MCP server and connects to available AI models
including Claude Desktop for local models and Ollama for additional options.
"""

import os
import sys
import json
import logging
import subprocess
import time
import requests
from dotenv import load_dotenv
from mcp_client import MCPClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("mcp_startup.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("mcp_startup")

# MCP Server configuration
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_API_KEY = os.getenv("MCP_API_KEY", "your-secret-api-key")
SERVER_URL = f"http://localhost:{MCP_PORT}"

# Default model configuration (Claude Desktop)
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "claude-desktop")
DEFAULT_MODEL_TYPE = os.getenv("DEFAULT_MODEL_TYPE", "claude")
DEFAULT_MODEL_CONFIG_STR = os.getenv("DEFAULT_MODEL_CONFIG", '{"api_url": "http://localhost:5000/api"}')
try:
    DEFAULT_MODEL_CONFIG = json.loads(DEFAULT_MODEL_CONFIG_STR)
except Exception as e:
    logger.error(f"Error parsing DEFAULT_MODEL_CONFIG: {str(e)}")
    DEFAULT_MODEL_CONFIG = {"api_url": "http://localhost:5000/api"}

# Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
CONNECT_OLLAMA_MODELS = os.getenv("CONNECT_OLLAMA_MODELS", "false").lower() == "true"

def start_mcp_server():
    """Start the MCP server"""
    logger.info("Starting MCP server...")
    
    # Check if the server is already running
    try:
        response = requests.get(f"{SERVER_URL}/list_models", 
                               headers={"Authorization": f"Bearer {MCP_API_KEY}"})
        if response.status_code == 200:
            logger.info("MCP server is already running")
            return True
    except requests.exceptions.ConnectionError:
        logger.info("MCP server is not running. Starting it now...")
    
    # Start the server
    try:
        # Using subprocess to run in the background
        process = subprocess.Popen(
            [sys.executable, "mcp_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for the server to start
        for _ in range(10):
            try:
                response = requests.get(f"{SERVER_URL}/list_models", 
                                      headers={"Authorization": f"Bearer {MCP_API_KEY}"})
                if response.status_code == 200:
                    logger.info("MCP server started successfully")
                    return True
            except requests.exceptions.ConnectionError:
                time.sleep(1)
        
        logger.error("Failed to start MCP server")
        return False
        
    except Exception as e:
        logger.error(f"Error starting MCP server: {str(e)}")
        return False

def check_ollama():
    """Check if Ollama is running and get available models"""
    logger.info("Checking Ollama service...")
    
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags")
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            
            logger.info(f"Ollama is running. Available models: {', '.join(model_names)}")
            return model_names
        else:
            logger.error(f"Ollama returned error: {response.status_code}")
            return []
            
    except requests.exceptions.ConnectionError:
        logger.error("Ollama service is not running")
        return []
    except Exception as e:
        logger.error(f"Error connecting to Ollama: {str(e)}")
        return []

def check_claude_desktop():
    """Check if Claude Desktop is running"""
    logger.info("Checking Claude Desktop service...")
    
    api_url = DEFAULT_MODEL_CONFIG.get("api_url", "http://localhost:5000/api")
    
    try:
        response = requests.get(f"{api_url}/models/info")
        
        if response.status_code == 200:
            model_info = response.json()
            logger.info(f"Claude Desktop is running. Model: {model_info.get('model_name', 'Unknown')}")
            return True
        else:
            logger.error(f"Claude Desktop returned error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("Claude Desktop service is not running")
        return False
    except Exception as e:
        logger.error(f"Error connecting to Claude Desktop: {str(e)}")
        return False

def connect_to_ollama_models(client, model_names):
    """Connect to Ollama models"""
    logger.info("Connecting to Ollama models...")
    
    connected_models = []
    
    for model_name in model_names:
        logger.info(f"Connecting to model: {model_name}")
        
        result = client.connect_model(
            model_name,
            "ollama",
            {"host": OLLAMA_HOST}
        )
        
        if result.get("success", False):
            logger.info(f"Successfully connected to model: {model_name}")
            connected_models.append(model_name)
        else:
            logger.error(f"Failed to connect to model {model_name}: {result.get('error')}")
    
    return connected_models

def connect_to_claude_desktop(client):
    """Connect to Claude Desktop"""
    logger.info("Connecting to Claude Desktop...")
    
    result = client.connect_model(
        DEFAULT_MODEL,
        DEFAULT_MODEL_TYPE,
        DEFAULT_MODEL_CONFIG
    )
    
    if result.get("success", False):
        logger.info(f"Successfully connected to Claude Desktop as {DEFAULT_MODEL}")
        return True
    else:
        logger.error(f"Failed to connect to Claude Desktop: {result.get('error')}")
        return False

def main():
    """Main function"""
    logger.info("Starting AI MCP startup script...")
    
    # Start MCP server
    if not start_mcp_server():
        logger.error("Failed to start MCP server. Exiting...")
        return
    
    # Initialize client
    client = MCPClient(SERVER_URL, MCP_API_KEY)
    
    # Connect to Claude Desktop (primary model)
    claude_desktop_available = check_claude_desktop()
    if claude_desktop_available:
        if connect_to_claude_desktop(client):
            logger.info("Claude Desktop is now the primary AI model")
        else:
            logger.warning("Failed to connect to Claude Desktop as the primary model")
            # Enable Ollama as fallback if Claude Desktop connection fails
            CONNECT_OLLAMA_MODELS = True
    else:
        logger.warning("Claude Desktop is not available. Checking Ollama models instead.")
        # Enable Ollama as fallback if Claude Desktop is not running
        CONNECT_OLLAMA_MODELS = True
    
    # Connect to Ollama models if enabled or as fallback
    if CONNECT_OLLAMA_MODELS:
        logger.info("Checking for available Ollama models...")
        model_names = check_ollama()
        
        if model_names:
            connected_models = connect_to_ollama_models(client, model_names)
            
            if connected_models:
                logger.info(f"Connected to Ollama models: {', '.join(connected_models)}")
                if not claude_desktop_available:
                    logger.info(f"Using {connected_models[0]} as primary AI model (Claude Desktop not available)")
            else:
                logger.warning("Failed to connect to any Ollama models")
        else:
            logger.warning("No Ollama models available")
    
    # Get list of connected models
    try:
        result = client.list_models()
        if result.get("success", False):
            models = result.get("models", [])
            if models:
                model_ids = [model["model_id"] for model in models]
                logger.info(f"Connected models: {', '.join(model_ids)}")
            else:
                logger.warning("No models connected. The MCP server is running but may have limited functionality.")
    except Exception as e:
        logger.error(f"Error listing connected models: {str(e)}")
    
    logger.info("AI MCP startup complete")
    logger.info(f"Server running at http://{MCP_HOST}:{MCP_PORT}")
    logger.info("Press Ctrl+C to stop")

if __name__ == "__main__":
    main()
