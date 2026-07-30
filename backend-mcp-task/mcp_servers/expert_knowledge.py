"""
Expert Knowledge MCP Server
Provides tools for accessing expert recommendations and historical guidance
using generic SQLite MCP database operations.
"""
from mcp_servers import MCPServer
from database import execute_query
from typing import List, Dict, Optional

# Create MCP server instance
expert_server = MCPServer("expert", "Expert Knowledge Server")

def search_expert_recommendations(category: str) -> List[Dict]:
    """Search expert recommendations by category using generic MCP query execution."""
    return execute_query("""
        SELECT * FROM expert_analysis
        WHERE LOWER(category) LIKE ?
        ORDER BY created_at DESC
    """, [f'%{category.lower()}%'])

def get_historical_guidance(task_type: Optional[str] = None) -> List[Dict]:
    """Get historical guidance and best practices using generic MCP query execution."""
    if task_type:
        return execute_query("""
            SELECT * FROM expert_analysis
            WHERE LOWER(category) LIKE ? OR LOWER(recommendation) LIKE ?
            ORDER BY created_at DESC
        """, [f'%{task_type.lower()}%', f'%{task_type.lower()}%'])
    else:
        return execute_query("""
            SELECT * FROM expert_analysis
            ORDER BY created_at DESC
            LIMIT 50
        """)

def get_expert_by_category() -> Dict:
    """Get all expert recommendations grouped by category using generic MCP query execution."""
    categories = execute_query("""
        SELECT category, COUNT(*) as count
        FROM expert_analysis
        GROUP BY category
        ORDER BY count DESC
    """)
    
    expert_knowledge = {}
    for cat in categories:
        category_name = cat['category']
        rows = execute_query("""
            SELECT * FROM expert_analysis
            WHERE category = ?
            ORDER BY created_at DESC
        """, [category_name])
        expert_knowledge[category_name] = rows
    
    return {
        "categories": categories,
        "knowledge_base": expert_knowledge
    }

# Register tools
expert_server.register_tool("search_expert_recommendations", search_expert_recommendations)
expert_server.register_tool("get_historical_guidance", get_historical_guidance)
expert_server.register_tool("get_expert_by_category", get_expert_by_category)
