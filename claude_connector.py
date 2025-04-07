"""
Claude Model Connector for MCP Server

This module provides integration between the MCP server and Claude models
via the Anthropic API.
"""

import os
import json
import requests
import logging
from typing import Dict, Any, Optional, List

# Configure logging
logger = logging.getLogger("claude_connector")

class ClaudeConnector:
    """Connector for Anthropic's Claude models"""
    
    def __init__(self, api_key: str, model_id: str = "claude-3-5-sonnet-20240620", base_url: str = "https://api.anthropic.com"):
        """
        Initialize Claude connector
        
        Args:
            api_key: Anthropic API key
            model_id: Claude model version (e.g., "claude-3-5-sonnet-20240620")
            base_url: API base URL
        """
        self.api_key = api_key
        self.model_id = model_id
        self.base_url = base_url
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> Dict[str, Any]:
        """
        Generate a response from Claude
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            
        Returns:
            Dictionary with model response
        """
        url = f"{self.base_url}/v1/messages"
        
        try:
            payload = {
                "model": self.model_id,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Extract the text response
            if "content" in result and len(result["content"]) > 0:
                response_text = result["content"][0]["text"]
                return {
                    "success": True,
                    "response": response_text,
                    "model_id": self.model_id,
                    "usage": result.get("usage", {})
                }
            else:
                return {
                    "success": False,
                    "error": "No content in response",
                    "raw_response": result
                }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Claude API error: {str(e)}")
            return {
                "success": False,
                "error": f"API request error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Claude connector error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the API is accessible
        
        Returns:
            Dictionary with health status
        """
        try:
            # Simple prompt to test connectivity
            result = self.generate("Hello, Claude. Please respond with only the word 'OK'.", max_tokens=10)
            
            if result.get("success", False):
                return {
                    "success": True,
                    "message": "Claude API is accessible",
                    "model_id": self.model_id
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "model_id": self.model_id
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_id": self.model_id
            }

# Factory function to create a Claude connector
def create_claude_connector(config: Dict[str, Any]) -> Optional[ClaudeConnector]:
    """
    Create a Claude connector from configuration
    
    Args:
        config: Configuration dictionary with:
            - api_key: Anthropic API key
            - model_id: (optional) Claude model version
            - base_url: (optional) API base URL
            
    Returns:
        ClaudeConnector instance or None if config is invalid
    """
    try:
        api_key = config.get("api_key")
        
        if not api_key:
            logger.error("Missing required configuration: api_key")
            return None
            
        model_id = config.get("model_id", "claude-3-5-sonnet-20240620")
        base_url = config.get("base_url", "https://api.anthropic.com")
        
        return ClaudeConnector(api_key, model_id, base_url)
        
    except Exception as e:
        logger.error(f"Error creating Claude connector: {str(e)}")
        return None
