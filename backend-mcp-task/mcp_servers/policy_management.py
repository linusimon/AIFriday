"""
Policy Management MCP Server
Provides tools for accessing policies, business rules, and escalation rules
using generic SQLite MCP database operations.
"""
from mcp_servers import MCPServer
from database import execute_query
from typing import List, Dict, Optional

# Create MCP server instance
policy_server = MCPServer("policy", "Policy Management Server")

def search_policies(query: str, category: Optional[str] = None) -> List[Dict]:
    """Search for policies using generic MCP query execution."""
    query_lower = query.lower()
    
    if category:
        return execute_query("""
            SELECT * FROM expert_analysis
            WHERE category = ? AND 
            (LOWER(recommendation) LIKE ? OR LOWER(notes) LIKE ? OR LOWER(category) LIKE ?)
            ORDER BY created_at DESC
        """, [category, f'%{query_lower}%', f'%{query_lower}%', f'%{query_lower}%'])
    else:
        return execute_query("""
            SELECT * FROM expert_analysis
            WHERE LOWER(recommendation) LIKE ? OR LOWER(notes) LIKE ? OR LOWER(category) LIKE ?
            ORDER BY created_at DESC
        """, [f'%{query_lower}%', f'%{query_lower}%', f'%{query_lower}%'])

def get_business_rules() -> Dict:
    """Get all business rules grouped by category using generic MCP query execution."""
    rules = execute_query("""
        SELECT * FROM expert_analysis
        ORDER BY category, created_at DESC
    """)
    
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
    """Get escalation rules using generic MCP query execution."""
    if priority:
        return execute_query("""
            SELECT * FROM sla_rules
            WHERE priority = ?
            ORDER BY target_duration
        """, [priority])
    else:
        return execute_query("""
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

# Register tools
policy_server.register_tool("search_policies", search_policies)
policy_server.register_tool("get_business_rules", get_business_rules)
policy_server.register_tool("get_escalation_rules", get_escalation_rules)
