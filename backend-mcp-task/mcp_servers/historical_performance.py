"""
Historical Performance MCP Server
Provides tools for accessing historical assignment data and performance metrics
using generic SQLite MCP database operations.
"""
from mcp_servers import MCPServer
from database import execute_query
from typing import List, Dict, Optional

# Create MCP server instance
performance_server = MCPServer("performance", "Historical Performance Server")

def get_historical_assignments(resource_id: Optional[int] = None, resource_type: str = 'human') -> List[Dict]:
    """Get historical assignment data using generic MCP query execution."""
    if resource_id:
        return execute_query("""
            SELECT 
                ha.*,
                t.task_name,
                t.complexity,
                t.skills_required
            FROM historical_assignments ha
            LEFT JOIN tasks t ON ha.task_id = t.task_id
            WHERE ha.resource_id = ? AND ha.resource_type = ?
            ORDER BY ha.created_at DESC
        """, [resource_id, resource_type.capitalize()])
    else:
        return execute_query("""
            SELECT 
                ha.*,
                t.task_name,
                t.complexity,
                t.skills_required
            FROM historical_assignments ha
            LEFT JOIN tasks t ON ha.task_id = t.task_id
            ORDER BY ha.created_at DESC
            LIMIT 100
        """)

def get_success_rates(resource_id: int, resource_type: str = 'human') -> Dict:
    """Get success rate metrics using generic MCP query execution."""
    rows = execute_query("""
        SELECT 
            COUNT(*) as total_assignments,
            SUM(CASE WHEN outcome = 'Success' THEN 1 ELSE 0 END) as successful,
            SUM(CASE WHEN outcome = 'Delayed' THEN 1 ELSE 0 END) as delayed,
            SUM(CASE WHEN outcome = 'Failed' THEN 1 ELSE 0 END) as failed,
            AVG(quality_score) as avg_quality,
            AVG(completion_time) as avg_completion_time
        FROM historical_assignments
        WHERE resource_id = ? AND resource_type = ?
    """, [resource_id, resource_type.capitalize()])
    
    stats = rows[0] if rows else {
        "total_assignments": 0, "successful": 0, "delayed": 0, "failed": 0, "avg_quality": 0, "avg_completion_time": 0
    }
    
    if stats.get('total_assignments', 0) > 0:
        stats['success_rate'] = round((stats['successful'] / stats['total_assignments']) * 100, 2)
    else:
        stats['success_rate'] = 0
    
    return stats

def get_quality_scores(resource_id: Optional[int] = None, resource_type: str = 'human') -> Dict:
    """Get quality score history using generic MCP query execution."""
    if resource_id:
        historical_rows = execute_query("""
            SELECT 
                resource_id,
                AVG(quality_score) as avg_quality_score,
                MIN(quality_score) as min_quality_score,
                MAX(quality_score) as max_quality_score,
                COUNT(*) as assignment_count
            FROM historical_assignments
            WHERE resource_id = ? AND resource_type = ?
            GROUP BY resource_id
        """, [resource_id, resource_type.capitalize()])
        historical = historical_rows[0] if historical_rows else {}
        
        if resource_type == 'human':
            current_rows = execute_query("""
                SELECT name, quality_score, performance_score
                FROM human_resources
                WHERE resource_id = ?
            """, [resource_id])
        else:
            current_rows = execute_query("""
                SELECT agent_name as name, quality_score, performance_score
                FROM ai_agents
                WHERE agent_id = ?
            """, [resource_id])
        
        current = current_rows[0] if current_rows else {}
        result = current
        if historical:
            result['historical_avg'] = historical.get('avg_quality_score')
            result['historical_min'] = historical.get('min_quality_score')
            result['historical_max'] = historical.get('max_quality_score')
            result['assignment_count'] = historical.get('assignment_count')
        
        return result
    else:
        return execute_query("""
            SELECT 
                resource_id,
                resource_type,
                AVG(quality_score) as avg_quality_score,
                COUNT(*) as assignment_count
            FROM historical_assignments
            GROUP BY resource_id, resource_type
            ORDER BY avg_quality_score DESC
        """)

# Register tools
performance_server.register_tool("get_historical_assignments", get_historical_assignments)
performance_server.register_tool("get_success_rates", get_success_rates)
performance_server.register_tool("get_quality_scores", get_quality_scores)
