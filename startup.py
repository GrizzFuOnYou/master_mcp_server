"""
AI MCP Server Startup Script

This script starts the AI MCP server and connects to available AI models
including Ollama for local models and Claude for cloud-based inference.
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

# Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
CONNECT_OLLAMA_MODELS = os.getenv("CONNECT_OLLAMA_MODELS", "true").lower() == "true"

# Claude configuration
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL_ID = os.getenv("CLAUDE_MODEL_ID", "claude-3-5-sonnet-20240620")
CLAUDE_BASE_URL = os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com")
CONNECT_CLAUDE = os.getenv("CONNECT_CLAUDE", "true").lower() == "true" and CLAUDE_API_KEY

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

def connect_to_claude(client):
    """Connect to Claude model"""
    if not CLAUDE_API_KEY:
        logger.warning("Claude API key not set. Skipping Claude connection.")
        return False
        
    logger.info(f"Connecting to Claude model: {CLAUDE_MODEL_ID}")
    
    # Prepare configuration
    config = {
        "api_key": CLAUDE_API_KEY,
        "model_id": CLAUDE_MODEL_ID,
        "base_url": CLAUDE_BASE_URL,
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    # Connect to Claude
    result = client.connect_model(
        CLAUDE_MODEL_ID,
        "claude",
        config
    )
    
    if result.get("success", False):
        logger.info(f"Successfully connected to Claude model: {CLAUDE_MODEL_ID}")
        return True
    else:
        logger.error(f"Failed to connect to Claude model: {result.get('error')}")
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
    
    # Connect to Claude as the default model (if enabled)
    if CONNECT_CLAUDE:
        if connect_to_claude(client):
            logger.info("Claude is now the default AI model")
        else:
            logger.warning("Failed to connect to Claude as the default model")
    
    # Connect to Ollama models if enabled
    if CONNECT_OLLAMA_MODELS:
        model_names = check_ollama()
        
        if model_names:
            connected_models = connect_to_ollama_models(client, model_names)
            
            if connected_models:
                logger.info(f"Connected to Ollama models: {', '.join(connected_models)}")
            else:
                logger.warning("Failed to connect to any Ollama models")
        else:
            logger.warning("No Ollama models available")
    
    logger.info("AI MCP startup complete")

if __name__ == "__main__":
    main()
