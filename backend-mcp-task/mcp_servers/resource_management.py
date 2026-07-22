"""
Resource Management MCP Server
Provides tools for accessing resource availability, workload, skills, and capacity
"""
from mcp_servers import MCPServer
from database import get_db_connection
from typing import Optional, List, Dict

# Create MCP server instance
resource_server = MCPServer("resource", "Resource Management Server")

def get_available_resources(resource_type: Optional[str] = None) -> List[Dict]:
    """
    Get all available resources
    
    Args:
        resource_type: Filter by 'human' or 'ai' (optional)
    
    Returns:
        List of available resources
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    resources = []
    
    # Get human resources
    if not resource_type or resource_type == 'human':
        cursor.execute("""
            SELECT 
                resource_id as id,
                name,
                role,
                skills,
                experience,
                availability,
                current_workload,
                quality_score,
                performance_score,
                cost_per_hour,
                'human' as type
            FROM human_resources
            WHERE availability = 'Available'
            ORDER BY name
        """)
        resources.extend([dict(row) for row in cursor.fetchall()])
    
    # Get AI agents
    if not resource_type or resource_type == 'ai':
        cursor.execute("""
            SELECT 
                agent_id as id,
                agent_name as name,
                capabilities as skills,
                specialization as role,
                availability,
                0 as experience,
                0 as current_workload,
                quality_score,
                performance_score,
                cost_per_hour,
                'ai' as type
            FROM ai_agents
            WHERE availability = 'Available'
            ORDER BY agent_name
        """)
        resources.extend([dict(row) for row in cursor.fetchall()])
    
    conn.close()
    return resources

def get_current_workload(resource_id: Optional[int] = None, resource_type: Optional[str] = 'human') -> List[Dict]:
    """
    Get current workload for resources
    
    Args:
        resource_id: Specific resource ID (optional)
        resource_type: 'human' or 'ai' (default: 'human')
    
    Returns:
        List of resources with workload information
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if resource_type == 'human':
        if resource_id:
            cursor.execute("""
                SELECT 
                    resource_id as id,
                    name,
                    role,
                    current_workload,
                    availability
                FROM human_resources
                WHERE resource_id = ?
            """, (resource_id,))
        else:
            cursor.execute("""
                SELECT 
                    resource_id as id,
                    name,
                    role,
                    current_workload,
                    availability
                FROM human_resources
                ORDER BY current_workload DESC
            """)
    else:  # AI agents
        cursor.execute("""
            SELECT 
                agent_id as id,
                agent_name as name,
                specialization as role,
                0 as current_workload,
                availability
            FROM ai_agents
            ORDER BY agent_name
        """)
    
    workload = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return workload

def get_resource_skills(resource_id: int, resource_type: str = 'human') -> Dict:
    """
    Get skills for a specific resource
    
    Args:
        resource_id: Resource ID
        resource_type: 'human' or 'ai'
    
    Returns:
        Resource details with skills
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if resource_type == 'human':
        cursor.execute("""
            SELECT 
                resource_id as id,
                name,
                role,
                skills,
                experience
            FROM human_resources
            WHERE resource_id = ?
        """, (resource_id,))
    else:  # AI agents
        cursor.execute("""
            SELECT 
                agent_id as id,
                agent_name as name,
                specialization as role,
                capabilities as skills,
                0 as experience
            FROM ai_agents
            WHERE agent_id = ?
        """, (resource_id,))
    
    resource = cursor.fetchone()
    conn.close()
    
    if resource:
        return dict(resource)
    else:
        return {"error": "Resource not found"}

def get_resource_capacity() -> Dict:
    """
    Get overall resource capacity and utilization metrics
    
    Returns:
        Capacity metrics for all resources
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Human resources capacity
    cursor.execute("""
        SELECT 
            COUNT(*) as total_count,
            SUM(CASE WHEN availability = 'Available' THEN 1 ELSE 0 END) as available_count,
            AVG(current_workload) as avg_workload,
            MAX(current_workload) as max_workload,
            MIN(current_workload) as min_workload
        FROM human_resources
    """)
    human_capacity = dict(cursor.fetchone())
    
    # AI agents capacity
    cursor.execute("""
        SELECT 
            COUNT(*) as total_count,
            SUM(CASE WHEN availability = 'Available' THEN 1 ELSE 0 END) as available_count
        FROM ai_agents
    """)
    ai_capacity = dict(cursor.fetchone())
    
    conn.close()
    
    return {
        "human_resources": human_capacity,
        "ai_agents": ai_capacity,
        "utilization_status": "High" if human_capacity['avg_workload'] > 70 else "Medium" if human_capacity['avg_workload'] > 40 else "Low"
    }

# Register tools
resource_server.register_tool("get_available_resources", get_available_resources)
resource_server.register_tool("get_current_workload", get_current_workload)
resource_server.register_tool("get_resource_skills", get_resource_skills)
resource_server.register_tool("get_resource_capacity", get_resource_capacity)
