"""
Cost Optimization MCP Server
Provides tools for cost estimation and assignment option comparison
"""
from mcp_servers import MCPServer
from database import get_db_connection
from typing import List, Dict

# Create MCP server instance
cost_server = MCPServer("cost", "Cost Optimization Server")

def estimate_assignment_cost(resource_id: int, resource_type: str, estimated_effort: float) -> Dict:
    """
    Estimate cost of assigning a task to a resource
    
    Args:
        resource_id: Resource ID
        resource_type: 'human' or 'ai'
        estimated_effort: Estimated effort in hours
    
    Returns:
        Cost estimation
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get resource cost
    if resource_type == 'human':
        cursor.execute("""
            SELECT name, role, cost_per_hour, quality_score, performance_score
            FROM human_resources
            WHERE resource_id = ?
        """, (resource_id,))
    else:
        cursor.execute("""
            SELECT agent_name as name, specialization as role, cost_per_hour, quality_score, performance_score
            FROM ai_agents
            WHERE agent_id = ?
        """, (resource_id,))
    
    resource = cursor.fetchone()
    conn.close()
    
    if not resource:
        return {"error": "Resource not found"}
    
    resource_dict = dict(resource)
    cost_per_hour = resource_dict['cost_per_hour']
    
    # Calculate total cost
    total_cost = cost_per_hour * estimated_effort
    
    # Calculate cost efficiency score (lower cost with higher quality is better)
    quality_score = resource_dict['quality_score']
    cost_efficiency = (quality_score / cost_per_hour) * 10 if cost_per_hour > 0 else 0
    
    return {
        "resource_id": resource_id,
        "resource_name": resource_dict['name'],
        "resource_type": resource_type,
        "cost_per_hour": cost_per_hour,
        "estimated_effort": estimated_effort,
        "total_cost": round(total_cost, 2),
        "quality_score": quality_score,
        "cost_efficiency_score": round(cost_efficiency, 2)
    }

def compare_assignment_options(resource_ids: str, resource_types: str, estimated_effort: float) -> List[Dict]:
    """
    Compare cost of multiple assignment options
    
    Args:
        resource_ids: Comma-separated list of resource IDs
        resource_types: Comma-separated list of resource types ('human' or 'ai')
        estimated_effort: Estimated effort in hours
    
    Returns:
        List of cost comparisons, sorted by cost efficiency
    """
    ids = [int(id.strip()) for id in resource_ids.split(',')]
    types = [t.strip() for t in resource_types.split(',')]
    
    if len(ids) != len(types):
        return {"error": "Resource IDs and types must have the same length"}
    
    comparisons = []
    
    for resource_id, resource_type in zip(ids, types):
        cost_estimate = estimate_assignment_cost(resource_id, resource_type, estimated_effort)
        if "error" not in cost_estimate:
            comparisons.append(cost_estimate)
    
    # Sort by cost efficiency (higher is better)
    comparisons.sort(key=lambda x: x['cost_efficiency_score'], reverse=True)
    
    # Add ranking
    for i, comp in enumerate(comparisons):
        comp['rank'] = i + 1
        comp['recommendation'] = "Best" if i == 0 else "Good" if i < len(comparisons) / 2 else "Consider alternatives"
    
    return comparisons

def get_cost_optimization_recommendations(task_id: int) -> Dict:
    """
    Get cost optimization recommendations for a task
    
    Args:
        task_id: Task ID
    
    Returns:
        Cost optimization recommendations
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get task details
    cursor.execute("""
        SELECT * FROM tasks WHERE task_id = ?
    """, (task_id,))
    
    task = cursor.fetchone()
    conn.close()
    
    if not task:
        return {"error": "Task not found"}
    
    task_dict = dict(task)
    estimated_effort = task_dict['estimated_effort']
    complexity = task_dict['complexity']
    
    # Provide recommendations based on complexity
    if complexity == 'Low':
        recommendation = "Consider AI agents for cost savings. They typically cost $8-12/hour vs $40-90/hour for humans."
        preferred_type = "ai"
    elif complexity == 'Medium':
        recommendation = "Balance cost and quality. Junior-Mid level developers ($40-60/hour) or specialized AI agents may be suitable."
        preferred_type = "mixed"
    else:  # High complexity
        recommendation = "Prioritize quality over cost. Senior resources ($70-90/hour) recommended despite higher cost."
        preferred_type = "human"
    
    return {
        "task_id": task_id,
        "complexity": complexity,
        "estimated_effort": estimated_effort,
        "recommendation": recommendation,
        "preferred_type": preferred_type,
        "cost_range": {
            "ai_agent": f"${estimated_effort * 8}-${estimated_effort * 12}",
            "junior_human": f"${estimated_effort * 40}-${estimated_effort * 60}",
            "senior_human": f"${estimated_effort * 70}-${estimated_effort * 90}"
        }
    }

# Register tools
cost_server.register_tool("estimate_assignment_cost", estimate_assignment_cost)
cost_server.register_tool("compare_assignment_options", compare_assignment_options)
cost_server.register_tool("get_cost_optimization_recommendations", get_cost_optimization_recommendations)
