"""
SLA Management MCP Server
Provides tools for SLA requirements and breach risk prediction
using generic SQLite MCP database operations.
"""
from mcp_servers import MCPServer
from database import execute_query
from typing import List, Dict, Optional

# Create MCP server instance
sla_server = MCPServer("sla", "SLA Management Server")

def get_sla_requirements(category: Optional[str] = None) -> List[Dict]:
    """Get SLA requirements using generic MCP query execution."""
    if category:
        return execute_query("""
            SELECT * FROM sla_rules
            WHERE category = ?
        """, [category])
    else:
        return execute_query("""
            SELECT * FROM sla_rules
            ORDER BY 
                CASE priority
                    WHEN 'Critical' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Medium' THEN 3
                    WHEN 'Low' THEN 4
                END
        """)

def predict_breach_risk(task_id: int, estimated_effort: float) -> Dict:
    """Predict SLA breach risk using generic MCP query execution."""
    tasks = execute_query("""
        SELECT t.*, p.sla, p.priority
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.project_id
        WHERE t.task_id = ?
    """, [task_id])
    
    if not tasks:
        return {"error": "Task not found"}
    
    task_dict = tasks[0]
    priority = task_dict.get('priority', 'Medium')
    
    sla_rules = execute_query("""
        SELECT * FROM sla_rules
        WHERE priority = ?
    """, [priority])
    
    if not sla_rules:
        return {
            "task_id": task_id,
            "priority": priority,
            "estimated_effort": estimated_effort,
            "risk_level": "Unknown",
            "message": "No SLA rule found for this priority"
        }
    
    sla_dict = sla_rules[0]
    target_duration_hours = sla_dict['target_duration']
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
    """Check SLA compliance using generic MCP query execution."""
    tasks = execute_query("""
        SELECT t.*, p.priority
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.project_id
        WHERE t.task_id = ?
    """, [task_id])
    
    if not tasks:
        return {"error": "Task not found"}
    
    task_dict = tasks[0]
    priority = task_dict.get('priority', 'Medium')
    
    sla_rules = execute_query("""
        SELECT * FROM sla_rules
        WHERE priority = ?
    """, [priority])
    
    if not sla_rules:
        return {
            "compliant": None,
            "message": "No SLA rule found"
        }
    
    sla_dict = sla_rules[0]
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
