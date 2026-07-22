"""
Base MCP Server class for creating modular MCP servers as Flask blueprints
"""
from flask import Blueprint, jsonify
from typing import Dict, Any, Callable
import traceback

class MCPServer:
    """
    Base class for MCP servers.
    Each MCP server is implemented as a Flask blueprint with registered tools.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.blueprint = Blueprint(f'mcp_{name}', __name__, url_prefix=f'/api/mcp/{name}')
        self.tools: Dict[str, Callable] = {}
        
        # Register status endpoint
        @self.blueprint.route('/status', methods=['GET'])
        def status():
            return jsonify({
                "success": True,
                "server": self.name,
                "description": self.description,
                "tools": list(self.tools.keys())
            })
    
    def register_tool(self, name: str, handler: Callable):
        """Register a tool with the MCP server"""
        self.tools[name] = handler
        
        # Create Flask route for the tool with unique endpoint name
        endpoint_name = f'{self.name}_{name}'
        
        @self.blueprint.route(f'/{name}', methods=['POST', 'GET'], endpoint=endpoint_name)
        def tool_handler():
            try:
                from flask import request
                # Get parameters from request (JSON body or query params)
                if request.method == 'POST':
                    params = request.get_json() or {}
                else:
                    params = request.args.to_dict()
                
                # Call the tool handler
                result = handler(**params)
                
                return jsonify({
                    "success": True,
                    "tool": name,
                    "result": result
                })
            except Exception as e:
                traceback.print_exc()
                return jsonify({
                    "success": False,
                    "tool": name,
                    "error": str(e)
                }), 500
    
    def get_blueprint(self):
        """Get the Flask blueprint for this MCP server"""
        return self.blueprint
