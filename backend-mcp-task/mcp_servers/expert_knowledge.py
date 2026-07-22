"""
Expert Knowledge MCP Server
Provides tools for accessing expert recommendations and historical guidance
"""
from mcp_servers import MCPServer
from database import get_db_connection
from typing import List, Dict, Optional

# Create MCP server instance
expert_server = MCPServer("expert", "Expert Knowledge Server")

def search_expert_recommendations(category: str) -> List[Dict]:
    """
    Search expert recommendations by category
    
    Args:
        category: Category to search (e.g., 'Backend Development', 'Security')
    
    Returns:
        List of expert recommendations
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM expert_analysis
        WHERE LOWER(category) LIKE ?
        ORDER BY created_at DESC
    """, (f'%{category.lower()}%',))
    
    recommendations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return recommendations

def get_historical_guidance(task_type: Optional[str] = None) -> List[Dict]:
    """
    Get historical guidance and best practices
    
    Args:
        task_type: Type of task (optional)
    
    Returns:
        List of historical guidance entries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if task_type:
        cursor.execute("""
            SELECT * FROM expert_analysis
            WHERE LOWER(category) LIKE ? OR LOWER(recommendation) LIKE ?
            ORDER BY created_at DESC
        """, (f'%{task_type.lower()}%', f'%{task_type.lower()}%'))
    else:
        cursor.execute("""
            SELECT * FROM expert_analysis
            ORDER BY created_at DESC
            LIMIT 50
        """)
    
    guidance = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return guidance

def get_expert_by_category() -> Dict:
    """
    Get all expert recommendations grouped by category
    
    Returns:
        Dictionary of recommendations by category
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM expert_analysis
        GROUP BY category
        ORDER BY count DESC
    """)
    
    categories = [dict(row) for row in cursor.fetchall()]
    
    # Get detailed recommendations for each category
    expert_knowledge = {}
    for cat in categories:
        category_name = cat['category']
        cursor.execute("""
            SELECT * FROM expert_analysis
            WHERE category = ?
            ORDER BY created_at DESC
        """, (category_name,))
        expert_knowledge[category_name] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "categories": categories,
        "knowledge_base": expert_knowledge
    }

# Register tools
expert_server.register_tool("search_expert_recommendations", search_expert_recommendations)
expert_server.register_tool("get_historical_guidance", get_historical_guidance)
expert_server.register_tool("get_expert_by_category", get_expert_by_category)
