#!/usr/bin/env python
"""
AI MCP Server Installation Script

This script automates the installation and initial setup of the AI MCP Server.
It installs dependencies, creates the necessary directory structure, and
sets up environment variables for easy deployment.
"""

import os
import sys
import subprocess
import logging
import shutil
import platform
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("mcp_install")

# Installation directory
DEFAULT_INSTALL_DIR = os.path.join(os.path.expanduser("~"), "ai_mcp_server")

# Claude Desktop is the default AI model
DEFAULT_MODEL = "claude-desktop"
DEFAULT_MODEL_TYPE = "claude"
DEFAULT_MODEL_CONFIG = {
    "api_url": "http://localhost:5000/api"
}

def check_python_version():
    """Check if Python version is compatible"""
    required_version = (3, 8)
    current_version = sys.version_info
    
    if current_version < required_version:
        logger.error(f"Python {required_version[0]}.{required_version[1]} or higher is required")
        logger.error(f"Current version: {current_version[0]}.{current_version[1]}")
        return False
    
    return True

def install_dependencies():
    """Install required Python packages"""
    logger.info("Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {str(e)}")
        return False

def create_directory_structure(install_dir):
    """Create the necessary directory structure"""
    logger.info(f"Creating directory structure in {install_dir}...")
    
    try:
        os.makedirs(os.path.join(install_dir, "models"), exist_ok=True)
        os.makedirs(os.path.join(install_dir, "examples"), exist_ok=True)
        os.makedirs(os.path.join(install_dir, "logs"), exist_ok=True)
        logger.info("Directory structure created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory structure: {str(e)}")
        return False

def copy_files(install_dir):
    """Copy files to installation directory"""
    logger.info("Copying files to installation directory...")
    
    try:
        # Copy main files
        for file in ["mcp_server.py", "mcp_client.py", "startup.py", "requirements.txt", ".env.example", "README.md"]:
            if os.path.exists(file):
                shutil.copy2(file, install_dir)
                
        # Copy models
        if os.path.exists("models"):
            for file in os.listdir("models"):
                if file.endswith(".py"):
                    shutil.copy2(os.path.join("models", file), os.path.join(install_dir, "models"))
                    
        # Copy examples
        if os.path.exists("examples"):
            for file in os.listdir("examples"):
                if file.endswith(".py"):
                    shutil.copy2(os.path.join("examples", file), os.path.join(install_dir, "examples"))
        
        logger.info("Files copied successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to copy files: {str(e)}")
        return False

def create_env_file(install_dir):
    """Create .env file with default settings"""
    logger.info("Creating .env file...")
    
    env_file = os.path.join(install_dir, ".env")
    
    try:
        with open(env_file, "w") as f:
            f.write(f"# AI MCP Server Configuration\n")
            f.write(f"# Created by install.py\n\n")
            f.write(f"# Server configuration\n")
            f.write(f"MCP_HOST=0.0.0.0\n")
            f.write(f"MCP_PORT=8000\n")
            f.write(f"MCP_API_KEY=your-secret-api-key\n\n")
            f.write(f"# Default model configuration\n")
            f.write(f"DEFAULT_MODEL={DEFAULT_MODEL}\n")
            f.write(f"DEFAULT_MODEL_TYPE={DEFAULT_MODEL_TYPE}\n")
            f.write(f"DEFAULT_MODEL_CONFIG={str(DEFAULT_MODEL_CONFIG)}\n\n")
            f.write(f"# Ollama configuration (if used)\n")
            f.write(f"OLLAMA_HOST=http://localhost:11434\n")
            f.write(f"CONNECT_OLLAMA_MODELS=false\n")
        
        logger.info(f"Environment file created at {env_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to create .env file: {str(e)}")
        return False

def create_startup_script(install_dir):
    """Create platform-specific startup script"""
    logger.info("Creating startup script...")
    
    if platform.system() == "Windows":
        script_path = os.path.join(install_dir, "start_mcp_server.bat")
        
        try:
            with open(script_path, "w") as f:
                f.write("@echo off\n")
                f.write("cd %~dp0\n")
                f.write(f"python startup.py\n")
                f.write("pause\n")
            
            logger.info(f"Windows startup script created at {script_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create Windows startup script: {str(e)}")
            return False
    else:
        script_path = os.path.join(install_dir, "start_mcp_server.sh")
        
        try:
            with open(script_path, "w") as f:
                f.write("#!/bin/bash\n")
                f.write(f"cd \"$(dirname \"$0\")\"\n")
                f.write(f"python3 startup.py\n")
            
            # Make script executable
            os.chmod(script_path, 0o755)
            
            logger.info(f"Unix startup script created at {script_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create Unix startup script: {str(e)}")
            return False

def main():
    """Main installation function"""
    logger.info("Starting AI MCP Server installation...")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Get installation directory
    install_dir = input(f"Enter installation directory [{DEFAULT_INSTALL_DIR}]: ").strip()
    if not install_dir:
        install_dir = DEFAULT_INSTALL_DIR
    
    # Create installation directory if it doesn't exist
    os.makedirs(install_dir, exist_ok=True)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create directory structure
    if not create_directory_structure(install_dir):
        sys.exit(1)
    
    # Copy files
    if not copy_files(install_dir):
        sys.exit(1)
    
    # Create .env file
    if not create_env_file(install_dir):
        sys.exit(1)
    
    # Create startup script
    if not create_startup_script(install_dir):
        sys.exit(1)
    
    logger.info(f"AI MCP Server installation completed successfully!")
    logger.info(f"Installation directory: {install_dir}")
    
    if platform.system() == "Windows":
        logger.info(f"To start the server, run {os.path.join(install_dir, 'start_mcp_server.bat')}")
    else:
        logger.info(f"To start the server, run {os.path.join(install_dir, 'start_mcp_server.sh')}")
    
    logger.info("Default AI model is set to Claude Desktop.")
    logger.info("You can change this in the .env file.")

if __name__ == "__main__":
    main()
