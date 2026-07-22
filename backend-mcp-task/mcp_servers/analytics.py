"""
Analytics MCP Server
Provides tools for similarity search, recommendations, and utilization metrics
"""
from mcp_servers import MCPServer
from database import get_db_connection
from typing import List, Dict, Optional

# Create MCP server instance
analytics_server = MCPServer("analytics", "Analytics Server")

def find_similar_tasks(task_description: str, limit: int = 5) -> List[Dict]:
    """
    Find similar tasks based on description
    
    Args:
        task_description: Task description to search
        limit: Maximum number of similar tasks to return
    
    Returns:
        List of similar tasks
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Simple keyword-based similarity search
    # In production, this would use embeddings and vector similarity
    keywords = set([word.lower() for word in task_description.split() if len(word) > 3])
    
    cursor.execute("""
        SELECT 
            t.*,
            p.project_name
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.project_id
    """)
    
    all_tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Calculate similarity scores
    scored_tasks = []
    for task in all_tasks:
        task_words = set([word.lower() for word in (task['description'] + ' ' + task['task_name']).split() if len(word) > 3])
        similarity = len(keywords & task_words) / len(keywords | task_words) if keywords | task_words else 0
        
        if similarity > 0:
            task['similarity_score'] = round(similarity * 100, 2)
            scored_tasks.append(task)
    
    # Sort by similarity and return top results
    scored_tasks.sort(key=lambda x: x['similarity_score'], reverse=True)
    return scored_tasks[:limit]

def recommend_best_resource(task_id: int) -> Dict:
    """
    Recommend the best resource for a task based on multiple factors
    
    Args:
        task_id: Task ID
    
    Returns:
        Resource recommendation
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get task details
    cursor.execute("""
        SELECT * FROM tasks WHERE task_id = ?
    """, (task_id,))
    
    task = cursor.fetchone()
    
    if not task:
        conn.close()
        return {"error": "Task not found"}
    
    task_dict = dict(task)
    required_skills = task_dict['skills_required']
    complexity = task_dict['complexity']
    estimated_effort = task_dict['estimated_effort']
    
    # Get all available resources with skill matching
    required_skill_set = set([s.strip().lower() for s in required_skills.split(',')])
    
    recommendations = []
    
    # Check human resources
    cursor.execute("""
        SELECT * FROM human_resources WHERE availability = 'Available'
    """)
    
    for row in cursor.fetchall():
        resource = dict(row)
        resource_skills = set([s.strip().lower() for s in resource['skills'].split(',')])
        
        # Calculate skill match score
        matched = required_skill_set & resource_skills
        skill_match = (len(matched) / len(required_skill_set)) * 100 if required_skill_set else 0
        
        # Calculate workload score (lower workload is better)
        workload_score = max(0, 100 - resource['current_workload'])
        
        # Calculate cost efficiency
        cost_efficiency = (resource['quality_score'] / resource['cost_per_hour']) * 10
        
        # Overall score (weighted combination)
        overall_score = (skill_match * 0.4 + 
                        resource['quality_score'] * 0.3 + 
                        workload_score * 0.2 + 
                        cost_efficiency * 0.1)
        
        if skill_match > 0:
            recommendations.append({
                "resource_id": resource['resource_id'],
                "name": resource['name'],
                "type": "human",
                "role": resource['role'],
                "skill_match_score": round(skill_match, 2),
                "quality_score": resource['quality_score'],
                "workload_score": round(workload_score, 2),
                "cost_per_hour": resource['cost_per_hour'],
                "overall_score": round(overall_score, 2)
            })
    
    # Check AI agents (if appropriate for complexity)
    if complexity in ['Low', 'Medium']:
        cursor.execute("""
            SELECT * FROM ai_agents WHERE availability = 'Available'
        """)
        
        for row in cursor.fetchall():
            agent = dict(row)
            agent_skills = set([s.strip().lower() for s in agent['capabilities'].split(',')])
            
            # Calculate skill match score
            matched = required_skill_set & agent_skills
            skill_match = (len(matched) / len(required_skill_set)) * 100 if required_skill_set else 0
            
            # AI agents always have 0 workload
            workload_score = 100
            
            # Calculate cost efficiency
            cost_efficiency = (agent['quality_score'] / agent['cost_per_hour']) * 10
            
            # Overall score (weighted combination)
            overall_score = (skill_match * 0.4 + 
                            agent['quality_score'] * 0.3 + 
                            workload_score * 0.2 + 
                            cost_efficiency * 0.1)
            
            if skill_match > 0:
                recommendations.append({
                    "resource_id": agent['agent_id'],
                    "name": agent['agent_name'],
                    "type": "ai",
                    "role": agent['specialization'],
                    "skill_match_score": round(skill_match, 2),
                    "quality_score": agent['quality_score'],
                    "workload_score": round(workload_score, 2),
                    "cost_per_hour": agent['cost_per_hour'],
                    "overall_score": round(overall_score, 2)
                })
    
    conn.close()
    
    # Sort by overall score
    recommendations.sort(key=lambda x: x['overall_score'], reverse=True)
    
    # Return top recommendation with alternatives
    if recommendations:
        return {
            "task_id": task_id,
            "complexity": complexity,
            "best_recommendation": recommendations[0],
            "alternatives": recommendations[1:min(4, len(recommendations))],
            "total_candidates": len(recommendations)
        }
    else:
        return {
            "task_id": task_id,
            "complexity": complexity,
            "message": "No suitable resources found",
            "total_candidates": 0
        }

def generate_utilization_metrics() -> Dict:
    """
    Generate resource utilization metrics
    
    Returns:
        Utilization statistics
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Human resource utilization
    cursor.execute("""
        SELECT 
            AVG(current_workload) as avg_workload,
            MAX(current_workload) as max_workload,
            MIN(current_workload) as min_workload,
            COUNT(*) as total_resources,
            SUM(CASE WHEN current_workload > 80 THEN 1 ELSE 0 END) as overloaded,
            SUM(CASE WHEN current_workload < 30 THEN 1 ELSE 0 END) as underutilized,
            SUM(CASE WHEN availability = 'Available' THEN 1 ELSE 0 END) as available
        FROM human_resources
    """)
    
    human_metrics = dict(cursor.fetchone())
    
    # Top performers
    cursor.execute("""
        SELECT name, role, quality_score, performance_score, current_workload
        FROM human_resources
        ORDER BY (quality_score + performance_score) / 2 DESC
        LIMIT 5
    """)
    
    top_performers = [dict(row) for row in cursor.fetchall()]
    
    # Workload distribution
    cursor.execute("""
        SELECT 
            name,
            role,
            current_workload,
            availability
        FROM human_resources
        ORDER BY current_workload DESC
    """)
    
    workload_distribution = [dict(row) for row in cursor.fetchall()]
    
    # Task statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_tasks,
            SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open_tasks,
            SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_tasks,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks,
            SUM(estimated_effort) as total_effort
        FROM tasks
    """)
    
    task_metrics = dict(cursor.fetchone())
    
    conn.close()
    
    return {
        "human_resources": human_metrics,
        "top_performers": top_performers,
        "workload_distribution": workload_distribution,
        "task_metrics": task_metrics,
        "recommendations": {
            "overloaded_count": human_metrics['overloaded'],
            "underutilized_count": human_metrics['underutilized'],
            "message": f"Consider redistributing work. {human_metrics['overloaded']} resources are overloaded (>80% capacity)."
        }
    }

# Register tools
analytics_server.register_tool("find_similar_tasks", find_similar_tasks)
analytics_server.register_tool("recommend_best_resource", recommend_best_resource)
analytics_server.register_tool("generate_utilization_metrics", generate_utilization_metrics)
