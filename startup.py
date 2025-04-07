"""
AI MCP Server Startup Script

This script starts the AI MCP server and connects to available Ollama models.
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

# Configuration
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_API_KEY = os.getenv("MCP_API_KEY", "your-secret-api-key")
SERVER_URL = f"http://localhost:{MCP_PORT}"

# Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
CONNECT_OLLAMA_MODELS = os.getenv("CONNECT_OLLAMA_MODELS", "true").lower() == "true"

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

def connect_to_models(client, model_names):
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

def main():
    """Main function"""
    logger.info("Starting AI MCP startup script...")
    
    # Start MCP server
    if not start_mcp_server():
        logger.error("Failed to start MCP server. Exiting...")
        return
    
    # Initialize client
    client = MCPClient(SERVER_URL, MCP_API_KEY)
    
    # Connect to Ollama models if enabled
    if CONNECT_OLLAMA_MODELS:
        model_names = check_ollama()
        
        if model_names:
            connected_models = connect_to_models(client, model_names)
            
            if connected_models:
                logger.info(f"Connected to models: {', '.join(connected_models)}")
            else:
                logger.warning("Failed to connect to any models")
        else:
            logger.warning("No Ollama models available")
    
    logger.info("AI MCP startup complete")

if __name__ == "__main__":
    main()
