"""
Policy Management MCP Server
Provides tools for accessing policies, business rules, and escalation rules
"""
from mcp_servers import MCPServer
from database import get_db_connection
from typing import List, Dict, Optional

# Create MCP server instance
policy_server = MCPServer("policy", "Policy Management Server")

def search_policies(query: str, category: Optional[str] = None) -> List[Dict]:
    """
    Search for policies and expert recommendations
    
    Args:
        query: Search query
        category: Filter by category (optional)
    
    Returns:
        List of matching policies
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query_lower = query.lower()
    
    if category:
        cursor.execute("""
            SELECT * FROM expert_analysis
            WHERE category = ? AND 
            (LOWER(recommendation) LIKE ? OR LOWER(notes) LIKE ? OR LOWER(category) LIKE ?)
            ORDER BY created_at DESC
        """, (category, f'%{query_lower}%', f'%{query_lower}%', f'%{query_lower}%'))
    else:
        cursor.execute("""
            SELECT * FROM expert_analysis
            WHERE LOWER(recommendation) LIKE ? OR LOWER(notes) LIKE ? OR LOWER(category) LIKE ?
            ORDER BY created_at DESC
        """, (f'%{query_lower}%', f'%{query_lower}%', f'%{query_lower}%'))
    
    policies = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return policies

def get_business_rules() -> List[Dict]:
    """
    Get all business rules and guidelines
    
    Returns:
        List of business rules
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM expert_analysis
        ORDER BY category, created_at DESC
    """)
    
    rules = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Group by category
    grouped = {}
    for rule in rules:
        category = rule['category']
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(rule)
    
    return {
        "rules_by_category": grouped,
        "total_rules": len(rules)
    }

def get_escalation_rules(priority: Optional[str] = None) -> List[Dict]:
    """
    Get escalation rules based on priority
    
    Args:
        priority: Filter by priority (optional)
    
    Returns:
        List of escalation rules
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if priority:
        cursor.execute("""
            SELECT * FROM sla_rules
            WHERE priority = ?
            ORDER BY target_duration
        """, (priority,))
    else:
        cursor.execute("""
            SELECT * FROM sla_rules
            ORDER BY 
                CASE priority
                    WHEN 'Critical' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Medium' THEN 3
                    WHEN 'Low' THEN 4
                END,
                target_duration
        """)
    
    rules = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rules

# Register tools
policy_server.register_tool("search_policies", search_policies)
policy_server.register_tool("get_business_rules", get_business_rules)
policy_server.register_tool("get_escalation_rules", get_escalation_rules)
