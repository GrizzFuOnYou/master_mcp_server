"""
Claude Desktop Connector Module for MCP Server

This module provides the integration between the MCP server and Claude Desktop,
enabling seamless interaction with the locally installed Claude AI.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List

# Configure logging
logger = logging.getLogger("claude_desktop")

class ClaudeDesktopConnector:
    """Connector for Claude Desktop AI application"""
    
    def __init__(self, api_url: str = "http://localhost:5000/api"):
        """
        Initialize the Claude Desktop connector
        
        Args:
            api_url: URL of the Claude Desktop API (default: http://localhost:5000/api)
        """
        self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json"
        }
        self.is_connected = False
        self.model_info = {}
        
    def connect(self) -> Dict[str, Any]:
        """
        Connect to Claude Desktop
        
        Returns:
            Dict with connection result
        """
        try:
            # Attempt to get model info
            response = requests.get(
                f"{self.api_url}/models/info",
                headers=self.headers
            )
            
            if response.status_code == 200:
                self.model_info = response.json()
                self.is_connected = True
                
                logger.info(f"Successfully connected to Claude Desktop: {self.model_info.get('model_name', 'Unknown')}")
                
                return {
                    "success": True,
                    "message": f"Connected to Claude Desktop",
                    "model_info": self.model_info
                }
            else:
                logger.error(f"Failed to connect to Claude Desktop: {response.status_code} - {response.text}")
                
                return {
                    "success": False,
                    "error": f"Connection failed: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error connecting to Claude Desktop: {str(e)}")
            
            return {
                "success": False,
                "error": str(e)
            }
            
    def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                temperature: float = 0.7, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Generate a response from Claude Desktop
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Temperature for generation (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dict with generation result
        """
        if not self.is_connected:
            return {
                "success": False,
                "error": "Not connected to Claude Desktop"
            }
            
        try:
            data = {
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if system_prompt:
                data["system_prompt"] = system_prompt
                
            response = requests.post(
                f"{self.api_url}/generate",
                headers=self.headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "metrics": {
                        "tokens": result.get("tokens", 0),
                        "model": self.model_info.get("model_name", "Claude")
                    }
                }
            else:
                logger.error(f"Failed to generate response: {response.status_code} - {response.text}")
                
                return {
                    "success": False,
                    "error": f"Generation failed: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            
            return {
                "success": False,
                "error": str(e)
            }
            
    def disconnect(self) -> Dict[str, Any]:
        """
        Disconnect from Claude Desktop
        
        Returns:
            Dict with disconnection result
        """
        self.is_connected = False
        self.model_info = {}
        
        return {
            "success": True,
            "message": "Disconnected from Claude Desktop"
        }

# Claude Desktop connection configuration
DEFAULT_CLAUDE_CONFIG = {
    "api_url": "http://localhost:5000/api",
    "model_id": "claude-desktop",
    "model_type": "claude"
}

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize connector
    connector = ClaudeDesktopConnector()
    
    # Connect to Claude Desktop
    result = connector.connect()
    print(f"Connection result: {result}")
    
    if result.get("success", False):
        # Generate a response
        generation_result = connector.generate("What is the capital of France?")
        print(f"Generation result: {generation_result}")
        
        # Disconnect
        disconnect_result = connector.disconnect()
        print(f"Disconnection result: {disconnect_result}")
