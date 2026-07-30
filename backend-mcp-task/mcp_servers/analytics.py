"""
Analytics MCP Server
Provides tools for similarity search, recommendations, and utilization metrics
using generic SQLite MCP database operations.
"""
from mcp_servers import MCPServer
from database import execute_query
from typing import List, Dict, Optional

# Create MCP server instance
analytics_server = MCPServer("analytics", "Analytics Server")

def find_similar_tasks(task_description: str, limit: int = 5) -> List[Dict]:
    """Find similar tasks using generic MCP query execution."""
    keywords = set([word.lower() for word in task_description.split() if len(word) > 3])
    all_tasks = execute_query("""
        SELECT 
            t.*,
            p.project_name
        FROM tasks t
        LEFT JOIN projects p ON t.project_id = p.project_id
    """)
    
    scored_tasks = []
    for task in all_tasks:
        desc_name = (task.get('description', '') or '') + ' ' + (task.get('task_name', '') or '')
        task_words = set([word.lower() for word in desc_name.split() if len(word) > 3])
        similarity = len(keywords & task_words) / len(keywords | task_words) if (keywords | task_words) else 0
        if similarity > 0:
            task['similarity_score'] = round(similarity * 100, 2)
            scored_tasks.append(task)
    
    scored_tasks.sort(key=lambda x: x['similarity_score'], reverse=True)
    return scored_tasks[:limit]

def recommend_best_resource(task_id: int) -> Dict:
    """Recommend the best resource for a task using generic MCP query execution."""
    tasks = execute_query("SELECT * FROM tasks WHERE task_id = ?", [task_id])
    if not tasks:
        return {"error": "Task not found"}
    
    task_dict = tasks[0]
    required_skills = task_dict['skills_required']
    complexity = task_dict['complexity']
    required_skill_set = set([s.strip().lower() for s in required_skills.split(',')])
    
    recommendations = []
    human_rows = execute_query("SELECT * FROM human_resources WHERE availability = 'Available'")
    
    for resource in human_rows:
        resource_skills = set([s.strip().lower() for s in resource['skills'].split(',')])
        matched = required_skill_set & resource_skills
        skill_match = (len(matched) / len(required_skill_set)) * 100 if required_skill_set else 0
        workload_score = max(0, 100 - resource['current_workload'])
        cost_efficiency = (resource['quality_score'] / resource['cost_per_hour']) * 10 if resource['cost_per_hour'] > 0 else 0
        overall_score = (skill_match * 0.4 + resource['quality_score'] * 0.3 + workload_score * 0.2 + cost_efficiency * 0.1)
        
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
    
    if complexity in ['Low', 'Medium']:
        ai_rows = execute_query("SELECT * FROM ai_agents WHERE availability = 'Available'")
        for agent in ai_rows:
            agent_skills = set([s.strip().lower() for s in agent['capabilities'].split(',')])
            matched = required_skill_set & agent_skills
            skill_match = (len(matched) / len(required_skill_set)) * 100 if required_skill_set else 0
            workload_score = 100
            cost_efficiency = (agent['quality_score'] / agent['cost_per_hour']) * 10 if agent['cost_per_hour'] > 0 else 0
            overall_score = (skill_match * 0.4 + agent['quality_score'] * 0.3 + workload_score * 0.2 + cost_efficiency * 0.1)
            
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
    
    recommendations.sort(key=lambda x: x['overall_score'], reverse=True)
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
    """Generate utilization metrics using generic MCP query execution."""
    human_metrics_rows = execute_query("""
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
    human_metrics = human_metrics_rows[0] if human_metrics_rows else {}
    
    top_performers = execute_query("""
        SELECT name, role, quality_score, performance_score, current_workload
        FROM human_resources
        ORDER BY (quality_score + performance_score) / 2 DESC
        LIMIT 5
    """)
    
    workload_distribution = execute_query("""
        SELECT 
            name,
            role,
            current_workload,
            availability
        FROM human_resources
        ORDER BY current_workload DESC
    """)
    
    task_metrics_rows = execute_query("""
        SELECT 
            COUNT(*) as total_tasks,
            SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open_tasks,
            SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_tasks,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks,
            SUM(estimated_effort) as total_effort
        FROM tasks
    """)
    task_metrics = task_metrics_rows[0] if task_metrics_rows else {}
    
    overloaded_cnt = human_metrics.get('overloaded') or 0
    underutilized_cnt = human_metrics.get('underutilized') or 0
    return {
        "human_resources": human_metrics,
        "top_performers": top_performers,
        "workload_distribution": workload_distribution,
        "task_metrics": task_metrics,
        "recommendations": {
            "overloaded_count": overloaded_cnt,
            "underutilized_count": underutilized_cnt,
            "message": f"Consider redistributing work. {overloaded_cnt} resources are overloaded (>80% capacity)."
        }
    }

# Register tools
analytics_server.register_tool("find_similar_tasks", find_similar_tasks)
analytics_server.register_tool("recommend_best_resource", recommend_best_resource)
analytics_server.register_tool("generate_utilization_metrics", generate_utilization_metrics)
