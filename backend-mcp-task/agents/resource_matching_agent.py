"""
Resource Matching Agent - Agent 5
Matches task requirements against available resources using MCP servers
"""
from agents import Agent
from typing import Dict, Any, List

class ResourceMatchingAgent(Agent):
    """
    Matches resources to tasks based on skills and availability.
    This agent runs in parallel with agents 6-9. No LLM call - uses MCP tools.
    """
    
    def __init__(self):
        super().__init__(
            name="ResourceMatchingAgent",
            description="Matches resources to tasks based on skills"
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match resources to classified tasks
        
        Args:
            context: Contains 'TaskClassificationAgent' results
        
        Returns:
            Resource recommendations for each task
        """
        self.log("Starting resource matching...")
        
        # Get classified tasks
        classification = context.get('TaskClassificationAgent', {})
        tasks = classification.get('classified_tasks', [])
        
        if not tasks:
            self.log("No tasks to match")
            return {
                "task_recommendations": [],
                "status": "no_data"
            }
        
        # Match resources for each task
        task_recommendations = []
        
        for i, task in enumerate(tasks):
            self.log(f"Matching resources for task {i+1}/{len(tasks)}: {task.get('task_name')}")
            recommendations = self.match_resources_for_task(task)
            task_recommendations.append(recommendations)
        
        return {
            "task_recommendations": task_recommendations,
            "total_tasks_matched": len(task_recommendations),
            "status": "success"
        }
    
    def match_resources_for_task(self, task: Dict) -> Dict:
        """Match resources for a single task using MCP servers"""
        
        required_skills = task.get('skills_required', '')
        complexity = task.get('complexity', 'Medium')
        
        # Call Skill Repository MCP server for skill matching
        skill_match_response = self.call_mcp_tool(
            'skill',
            'match_skills',
            {'required_skills': required_skills}
        )
        
        if not skill_match_response.get('success'):
            self.log(f"Skill matching failed: {skill_match_response.get('error')}")
            return {
                "task_name": task.get('task_name'),
                "recommendations": [],
                "error": "Skill matching failed"
            }
        
        matched_resources = skill_match_response.get('result', [])
        
        # Call Analytics MCP server for best recommendation
        analytics_response = self.call_mcp_tool(
            'analytics',
            'recommend_best_resource',
            {'task_id': task.get('task_id', 0)}
        )
        
        # Rank resources by match score
        ranked_resources = sorted(
            matched_resources,
            key=lambda x: x.get('match_score', 0),
            reverse=True
        )[:10]  # Top 10 matches
        
        return {
            "task_name": task.get('task_name'),
            "task_id": task.get('task_id'),
            "required_skills": required_skills,
            "complexity": complexity,
            "matched_resources": ranked_resources,
            "top_recommendation": ranked_resources[0] if ranked_resources else None,
            "total_matches": len(matched_resources)
        }
