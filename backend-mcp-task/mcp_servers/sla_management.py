"""
SLA Management MCP Server
Provides tools for SLA requirements and breach risk prediction
"""
from mcp_servers import MCPServer
from database import get_db_connection
from typing import List, Dict, Optional

# Create MCP server instance
sla_server = MCPServer("sla", "SLA Management Server")

def get_sla_requirements(category: Optional[str] = None) -> List[Dict]:
    """
    Get SLA requirements
    
    Args:
        category: Filter by category (optional)
    
    Returns:
        List of SLA rules
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if category:
        cursor.execute("""
            SELECT * FROM sla_rules
            WHERE category = ?
        """, (category,))
    else:
        cursor.execute("""
            SELECT * FROM sla_rules
            ORDER BY 
                CASE priority
                    WHEN 'Critical' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Medium' THEN 3
                    WHEN 'Low' THEN 4
                END
        """)
    
    rules = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rules

def predict_breach_risk(task_id: int, estimated_effort: float) -> Dict:
    """
    Predict SLA breach risk for a task
    
    Args:
        task_id: Task ID
        estimated_effort: Estimated effort in hours
    
    Returns:
        Breach risk assessment
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get task details
    cursor.execute("""
        SELECT t.*, p.sla, p.priority
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.project_id
        WHERE t.task_id = ?
    """, (task_id,))
    
    task = cursor.fetchone()
    
    if not task:
        conn.close()
        return {"error": "Task not found"}
    
    task_dict = dict(task)
    priority = task_dict['priority']
    
    # Get SLA rule for this priority
    cursor.execute("""
        SELECT * FROM sla_rules
        WHERE priority = ?
    """, (priority,))
    
    sla_rule = cursor.fetchone()
    conn.close()
    
    if not sla_rule:
        return {
            "task_id": task_id,
            "priority": priority,
            "estimated_effort": estimated_effort,
            "risk_level": "Unknown",
            "message": "No SLA rule found for this priority"
        }
    
    sla_dict = dict(sla_rule)
    target_duration_hours = sla_dict['target_duration']
    
    # Calculate risk based on effort vs target duration
    # Risk is High if effort > 80% of target, Medium if > 60%, Low otherwise
    effort_ratio = estimated_effort / target_duration_hours
    
    if effort_ratio >= 0.8:
        risk_level = "High"
        message = f"Estimated effort ({estimated_effort}h) is {round(effort_ratio*100)}% of SLA target ({target_duration_hours}h). High risk of breach."
    elif effort_ratio >= 0.6:
        risk_level = "Medium"
        message = f"Estimated effort ({estimated_effort}h) is {round(effort_ratio*100)}% of SLA target ({target_duration_hours}h). Moderate risk."
    else:
        risk_level = "Low"
        message = f"Estimated effort ({estimated_effort}h) is {round(effort_ratio*100)}% of SLA target ({target_duration_hours}h). Low risk of breach."
    
    return {
        "task_id": task_id,
        "priority": priority,
        "estimated_effort": estimated_effort,
        "target_duration": target_duration_hours,
        "effort_ratio": round(effort_ratio, 2),
        "risk_level": risk_level,
        "message": message,
        "escalation_rule": sla_dict['escalation_rule']
    }

def check_sla_compliance(task_id: int, actual_completion_time: float) -> Dict:
    """
    Check if a completed task met SLA requirements
    
    Args:
        task_id: Task ID
        actual_completion_time: Actual completion time in hours
    
    Returns:
        SLA compliance status
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get task details
    cursor.execute("""
        SELECT t.*, p.priority
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.project_id
        WHERE t.task_id = ?
    """, (task_id,))
    
    task = cursor.fetchone()
    
    if not task:
        conn.close()
        return {"error": "Task not found"}
    
    task_dict = dict(task)
    priority = task_dict['priority']
    
    # Get SLA rule
    cursor.execute("""
        SELECT * FROM sla_rules
        WHERE priority = ?
    """, (priority,))
    
    sla_rule = cursor.fetchone()
    conn.close()
    
    if not sla_rule:
        return {
            "compliant": None,
            "message": "No SLA rule found"
        }
    
    sla_dict = dict(sla_rule)
    target_duration = sla_dict['target_duration']
    
    compliant = actual_completion_time <= target_duration
    
    return {
        "task_id": task_id,
        "priority": priority,
        "target_duration": target_duration,
        "actual_completion_time": actual_completion_time,
        "compliant": compliant,
        "variance": actual_completion_time - target_duration,
        "message": "SLA met" if compliant else "SLA breached"
    }

# Register tools
sla_server.register_tool("get_sla_requirements", get_sla_requirements)
sla_server.register_tool("predict_breach_risk", predict_breach_risk)
sla_server.register_tool("check_sla_compliance", check_sla_compliance)
