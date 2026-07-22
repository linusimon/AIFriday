"""
Historical Performance MCP Server
Provides tools for accessing historical assignment data and performance metrics
"""
from mcp_servers import MCPServer
from database import get_db_connection
from typing import List, Dict, Optional

# Create MCP server instance
performance_server = MCPServer("performance", "Historical Performance Server")

def get_historical_assignments(resource_id: Optional[int] = None, resource_type: str = 'human') -> List[Dict]:
    """
    Get historical assignment data
    
    Args:
        resource_id: Specific resource ID (optional)
        resource_type: 'human' or 'ai'
    
    Returns:
        List of historical assignments
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if resource_id:
        cursor.execute("""
            SELECT 
                ha.*,
                t.task_name,
                t.complexity,
                t.skills_required
            FROM historical_assignments ha
            LEFT JOIN tasks t ON ha.task_id = t.task_id
            WHERE ha.resource_id = ? AND ha.resource_type = ?
            ORDER BY ha.created_at DESC
        """, (resource_id, resource_type.capitalize()))
    else:
        cursor.execute("""
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
    
    assignments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return assignments

def get_success_rates(resource_id: int, resource_type: str = 'human') -> Dict:
    """
    Get success rate metrics for a specific resource
    
    Args:
        resource_id: Resource ID
        resource_type: 'human' or 'ai'
    
    Returns:
        Success rate statistics
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_assignments,
            SUM(CASE WHEN outcome = 'Success' THEN 1 ELSE 0 END) as successful,
            SUM(CASE WHEN outcome = 'Delayed' THEN 1 ELSE 0 END) as delayed,
            SUM(CASE WHEN outcome = 'Failed' THEN 1 ELSE 0 END) as failed,
            AVG(quality_score) as avg_quality,
            AVG(completion_time) as avg_completion_time
        FROM historical_assignments
        WHERE resource_id = ? AND resource_type = ?
    """, (resource_id, resource_type.capitalize()))
    
    stats = dict(cursor.fetchone())
    conn.close()
    
    if stats['total_assignments'] > 0:
        stats['success_rate'] = round((stats['successful'] / stats['total_assignments']) * 100, 2)
    else:
        stats['success_rate'] = 0
    
    return stats

def get_quality_scores(resource_id: Optional[int] = None, resource_type: str = 'human') -> List[Dict]:
    """
    Get quality score history
    
    Args:
        resource_id: Specific resource ID (optional)
        resource_type: 'human' or 'ai'
    
    Returns:
        Quality score data
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if resource_id:
        # Get historical quality scores from assignments
        cursor.execute("""
            SELECT 
                resource_id,
                AVG(quality_score) as avg_quality_score,
                MIN(quality_score) as min_quality_score,
                MAX(quality_score) as max_quality_score,
                COUNT(*) as assignment_count
            FROM historical_assignments
            WHERE resource_id = ? AND resource_type = ?
            GROUP BY resource_id
        """, (resource_id, resource_type.capitalize()))
        
        historical = cursor.fetchone()
        
        # Get current quality score from resource table
        if resource_type == 'human':
            cursor.execute("""
                SELECT name, quality_score, performance_score
                FROM human_resources
                WHERE resource_id = ?
            """, (resource_id,))
        else:
            cursor.execute("""
                SELECT agent_name as name, quality_score, performance_score
                FROM ai_agents
                WHERE agent_id = ?
            """, (resource_id,))
        
        current = cursor.fetchone()
        conn.close()
        
        result = dict(current) if current else {}
        if historical:
            result['historical_avg'] = historical['avg_quality_score']
            result['historical_min'] = historical['min_quality_score']
            result['historical_max'] = historical['max_quality_score']
            result['assignment_count'] = historical['assignment_count']
        
        return result
    else:
        # Get quality scores for all resources
        cursor.execute("""
            SELECT 
                resource_id,
                resource_type,
                AVG(quality_score) as avg_quality_score,
                COUNT(*) as assignment_count
            FROM historical_assignments
            GROUP BY resource_id, resource_type
            ORDER BY avg_quality_score DESC
        """)
        
        scores = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return scores

# Register tools
performance_server.register_tool("get_historical_assignments", get_historical_assignments)
performance_server.register_tool("get_success_rates", get_success_rates)
performance_server.register_tool("get_quality_scores", get_quality_scores)
