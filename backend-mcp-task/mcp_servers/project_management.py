"""
Project Management MCP Server
Provides tools for accessing project and task information
using generic SQLite MCP database operations.
"""
from mcp_servers import MCPServer
from database import execute_query
from typing import List, Dict, Optional

# Create MCP server instance
project_server = MCPServer("project", "Project Management Server")

def get_project_details(project_id: int) -> Dict:
    """Get detailed information about a specific project using generic MCP query execution."""
    projects = execute_query("SELECT * FROM projects WHERE project_id = ?", [project_id])
    if not projects:
        return {"error": "Project not found"}
    
    project_dict = projects[0]
    tasks = execute_query("SELECT * FROM tasks WHERE project_id = ?", [project_id])
    
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t['status'] == 'Completed'])
    open_tasks = len([t for t in tasks if t['status'] == 'Open'])
    in_progress_tasks = len([t for t in tasks if t['status'] == 'In Progress'])
    total_effort = sum([t['estimated_effort'] for t in tasks])
    
    project_dict['tasks'] = tasks
    project_dict['statistics'] = {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "open_tasks": open_tasks,
        "in_progress_tasks": in_progress_tasks,
        "total_estimated_effort": total_effort,
        "completion_percentage": round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 2)
    }
    
    return project_dict

def get_project_status(project_id: Optional[int] = None) -> List[Dict]:
    """Get status of projects using generic MCP query execution."""
    if project_id:
        rows = execute_query("""
            SELECT 
                p.*,
                COUNT(t.task_id) as total_tasks,
                SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(t.estimated_effort) as total_effort
            FROM projects p
            LEFT JOIN tasks t ON p.project_id = t.project_id
            WHERE p.project_id = ?
            GROUP BY p.project_id
        """, [project_id])
    else:
        rows = execute_query("""
            SELECT 
                p.*,
                COUNT(t.task_id) as total_tasks,
                SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(t.estimated_effort) as total_effort
            FROM projects p
            LEFT JOIN tasks t ON p.project_id = t.project_id
            GROUP BY p.project_id
            ORDER BY 
                CASE p.priority
                    WHEN 'Critical' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Medium' THEN 3
                    WHEN 'Low' THEN 4
                END
        """)
    
    projects = []
    for project in rows:
        tot = project.get('total_tasks') or 0
        comp = project.get('completed_tasks') or 0
        if tot > 0:
            project['completion_percentage'] = round((comp / tot) * 100, 2)
        else:
            project['completion_percentage'] = 0
        projects.append(project)
    
    return projects

def get_task_information(task_id: int) -> Dict:
    """Get detailed information about a specific task using generic MCP query execution."""
    tasks = execute_query("""
        SELECT 
            t.*,
            p.project_name,
            p.priority as project_priority,
            p.business_area
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.project_id
        WHERE t.task_id = ?
    """, [task_id])
    
    if not tasks:
        return {"error": "Task not found"}
    
    task_dict = tasks[0]
    history = execute_query("SELECT * FROM historical_assignments WHERE task_id = ?", [task_id])
    task_dict['assignment_history'] = history
    
    decisions = execute_query("""
        SELECT * FROM routing_decisions
        WHERE task_id = ?
        ORDER BY created_at DESC
        LIMIT 5
    """, [task_id])
    task_dict['routing_decisions'] = decisions
    
    return task_dict

def get_tasks_by_status(status: str) -> List[Dict]:
    """Get tasks filtered by status using generic MCP query execution."""
    return execute_query("""
        SELECT 
            t.*,
            p.project_name
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.project_id
        WHERE t.status = ?
        ORDER BY t.priority DESC, t.created_at
    """, [status])

# Register tools
project_server.register_tool("get_project_details", get_project_details)
project_server.register_tool("get_project_status", get_project_status)
project_server.register_tool("get_task_information", get_task_information)
project_server.register_tool("get_tasks_by_status", get_tasks_by_status)
