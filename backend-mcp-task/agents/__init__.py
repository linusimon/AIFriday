"""
Base Agent class for multi-agent orchestration system
"""
import requests
from typing import Dict, Any, Optional, List
from config import Config
import json

class Agent:
    """
    Base class for all agents in the task routing system.
    Provides common functionality for LLM calls and MCP tool invocation.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.llm_api_url = f"{Config.GENAI_BASE_URL}v1/chat/completions"
        self.api_key = Config.GENAI_API_KEY
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main logic.
        To be overridden by subclasses.
        
        Args:
            context: Shared context dictionary with data from previous agents
        
        Returns:
            Result dictionary to be added to context
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    def call_llm(self, system_prompt: str, user_message: str, temperature: float = 0.7, response_format: Optional[str] = None) -> str:
        """
        Call TCS GenAI LLM
        
        Args:
            system_prompt: System prompt for the LLM
            user_message: User message/query
            temperature: Temperature for response generation
            response_format: Optional format specification (e.g., 'json')
        
        Returns:
            LLM response text
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        payload = {
            "model": Config.CHAT_MODEL,
            "messages": messages,
            "temperature": temperature
        }
        
        if response_format == 'json':
            payload["response_format"] = {"type": "json_object"}
        
        try:
            response = requests.post(
                self.llm_api_url,
                headers=headers,
                json=payload,
                verify=False,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Clean content if response_format is json or if it looks like markdown json
            if response_format == 'json' or (content and content.strip().startswith('```')):
                cleaned = content.strip()
                if cleaned.startswith('```json'):
                    cleaned = cleaned[7:]
                elif cleaned.startswith('```'):
                    cleaned = cleaned[3:]
                if cleaned.endswith('```'):
                    cleaned = cleaned[:-3]
                content = cleaned.strip()
                
            return content
        
        except Exception as e:
            print(f"[{self.name}] LLM call failed: {str(e)}")
            return f"Error: {str(e)}"
    
    def call_mcp_tool(self, server: str, tool: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call an MCP server tool
        
        Args:
            server: MCP server name (e.g., 'resource', 'skill')
            tool: Tool name (e.g., 'get_available_resources')
            params: Tool parameters
        
        Returns:
            Tool response
        """
        url = f"http://localhost:{Config.FLASK_PORT}/api/mcp/{server}/{tool}"
        
        try:
            if params:
                response = requests.post(url, json=params, timeout=30)
            else:
                response = requests.get(url, timeout=30)
            
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            print(f"[{self.name}] MCP tool call failed: {server}/{tool} - {str(e)}")
            return {"success": False, "error": str(e)}
    
    def log(self, message: str):
        """Log a message with agent name prefix"""
        print(f"[{self.name}] {message}")
