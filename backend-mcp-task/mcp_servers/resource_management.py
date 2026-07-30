"""
Resource Management MCP Server
Provides tools for accessing resource availability, workload, skills, and capacity
using generic SQLite MCP database operations.
"""
from mcp_servers import MCPServer
from database import execute_query, execute_statement
from typing import Optional, List, Dict

# Create MCP server instance
resource_server = MCPServer("resource", "Resource Management Server")

def get_available_resources(resource_type: Optional[str] = None) -> List[Dict]:
    """Get all available resources using generic MCP query execution."""
    resources = []
    
    # Get human resources
    if not resource_type or resource_type == 'human':
        human_rows = execute_query("""
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
        resources.extend(human_rows)
    
    # Get AI agents
    if not resource_type or resource_type == 'ai':
        ai_rows = execute_query("""
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
        resources.extend(ai_rows)
    
    return resources

def get_current_workload(resource_id: Optional[int] = None, resource_type: Optional[str] = 'human') -> List[Dict]:
    """Get current workload for resources using generic MCP query execution."""
    if resource_type == 'human':
        if resource_id:
            return execute_query("""
                SELECT 
                    resource_id as id,
                    name,
                    role,
                    current_workload,
                    availability
                FROM human_resources
                WHERE resource_id = ?
            """, [resource_id])
        else:
            return execute_query("""
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
        return execute_query("""
            SELECT 
                agent_id as id,
                agent_name as name,
                specialization as role,
                0 as current_workload,
                availability
            FROM ai_agents
            ORDER BY agent_name
        """)

def get_resource_skills(resource_id: int, resource_type: str = 'human') -> Dict:
    """Get skills for a specific resource using generic MCP query execution."""
    if resource_type == 'human':
        rows = execute_query("""
            SELECT 
                resource_id as id,
                name,
                role,
                skills,
                experience
            FROM human_resources
            WHERE resource_id = ?
        """, [resource_id])
    else:  # AI agents
        rows = execute_query("""
            SELECT 
                agent_id as id,
                agent_name as name,
                specialization as role,
                capabilities as skills,
                0 as experience
            FROM ai_agents
            WHERE agent_id = ?
        """, [resource_id])
    
    if rows:
        return rows[0]
    else:
        return {"error": "Resource not found"}

def get_resource_capacity() -> Dict:
    """Get overall resource capacity and utilization metrics using generic MCP query execution."""
    human_capacity_rows = execute_query("""
        SELECT 
            COUNT(*) as total_count,
            SUM(CASE WHEN availability = 'Available' THEN 1 ELSE 0 END) as available_count,
            AVG(current_workload) as avg_workload,
            MAX(current_workload) as max_workload,
            MIN(current_workload) as min_workload
        FROM human_resources
    """)
    human_capacity = human_capacity_rows[0] if human_capacity_rows else {}
    
    ai_capacity_rows = execute_query("""
        SELECT 
            COUNT(*) as total_count,
            SUM(CASE WHEN availability = 'Available' THEN 1 ELSE 0 END) as available_count
        FROM ai_agents
    """)
    ai_capacity = ai_capacity_rows[0] if ai_capacity_rows else {}
    
    avg_wl = human_capacity.get('avg_workload') or 0
    return {
        "human_resources": human_capacity,
        "ai_agents": ai_capacity,
        "utilization_status": "High" if avg_wl > 70 else "Medium" if avg_wl > 40 else "Low"
    }

# Register tools
resource_server.register_tool("get_available_resources", get_available_resources)
resource_server.register_tool("get_current_workload", get_current_workload)
resource_server.register_tool("get_resource_skills", get_resource_skills)
resource_server.register_tool("get_resource_capacity", get_resource_capacity)
