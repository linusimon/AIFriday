"""
Project Management MCP Server
Provides tools for accessing project and task information
"""
from mcp_servers import MCPServer
from database import get_db_connection
from typing import List, Dict, Optional

# Create MCP server instance
project_server = MCPServer("project", "Project Management Server")

def get_project_details(project_id: int) -> Dict:
    """
    Get detailed information about a specific project
    
    Args:
        project_id: Project ID
    
    Returns:
        Project details
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get project details
    cursor.execute("""
        SELECT * FROM projects WHERE project_id = ?
    """, (project_id,))
    
    project = cursor.fetchone()
    
    if not project:
        conn.close()
        return {"error": "Project not found"}
    
    project_dict = dict(project)
    
    # Get tasks for this project
    cursor.execute("""
        SELECT * FROM tasks WHERE project_id = ?
    """, (project_id,))
    
    tasks = [dict(row) for row in cursor.fetchall()]
    
    # Get task statistics
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t['status'] == 'Completed'])
    open_tasks = len([t for t in tasks if t['status'] == 'Open'])
    in_progress_tasks = len([t for t in tasks if t['status'] == 'In Progress'])
    
    total_effort = sum([t['estimated_effort'] for t in tasks])
    
    conn.close()
    
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
    """
    Get status of projects
    
    Args:
        project_id: Specific project ID (optional)
    
    Returns:
        List of project statuses
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if project_id:
        cursor.execute("""
            SELECT 
                p.*,
                COUNT(t.task_id) as total_tasks,
                SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(t.estimated_effort) as total_effort
            FROM projects p
            LEFT JOIN tasks t ON p.project_id = t.project_id
            WHERE p.project_id = ?
            GROUP BY p.project_id
        """, (project_id,))
    else:
        cursor.execute("""
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
    for row in cursor.fetchall():
        project = dict(row)
        if project['total_tasks'] > 0:
            project['completion_percentage'] = round((project['completed_tasks'] / project['total_tasks']) * 100, 2)
        else:
            project['completion_percentage'] = 0
        projects.append(project)
    
    conn.close()
    return projects

def get_task_information(task_id: int) -> Dict:
    """
    Get detailed information about a specific task
    
    Args:
        task_id: Task ID
    
    Returns:
        Task details
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get task with project info
    cursor.execute("""
        SELECT 
            t.*,
            p.project_name,
            p.priority as project_priority,
            p.business_area
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.project_id
        WHERE t.task_id = ?
    """, (task_id,))
    
    task = cursor.fetchone()
    
    if not task:
        conn.close()
        return {"error": "Task not found"}
    
    task_dict = dict(task)
    
    # Get historical assignments for this task
    cursor.execute("""
        SELECT * FROM historical_assignments
        WHERE task_id = ?
    """, (task_id,))
    
    history = [dict(row) for row in cursor.fetchall()]
    task_dict['assignment_history'] = history
    
    # Get routing decisions for this task
    cursor.execute("""
        SELECT * FROM routing_decisions
        WHERE task_id = ?
        ORDER BY created_at DESC
        LIMIT 5
    """, (task_id,))
    
    decisions = [dict(row) for row in cursor.fetchall()]
    task_dict['routing_decisions'] = decisions
    
    conn.close()
    return task_dict

def get_tasks_by_status(status: str) -> List[Dict]:
    """
    Get tasks filtered by status
    
    Args:
        status: Task status ('Open', 'In Progress', 'Completed', 'On Hold')
    
    Returns:
        List of tasks with the specified status
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            t.*,
            p.project_name
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.project_id
        WHERE t.status = ?
        ORDER BY t.priority DESC, t.created_at
    """, (status,))
    
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tasks

# Register tools
project_server.register_tool("get_project_details", get_project_details)
project_server.register_tool("get_project_status", get_project_status)
project_server.register_tool("get_task_information", get_task_information)
project_server.register_tool("get_tasks_by_status", get_tasks_by_status)
