"""
Cost Optimization Agent - Agent 7
Analyzes and optimizes assignment costs
"""
from agents import Agent
from typing import Dict, Any, List

class CostOptimizationAgent(Agent):
    """
    Optimizes task assignments based on cost efficiency.
    This agent runs in parallel with agents 5-6, 8-9. No LLM call - uses MCP tools.
    """
    
    def __init__(self):
        super().__init__(
            name="CostOptimizationAgent",
            description="Optimizes cost of task assignments"
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze costs and provide optimization recommendations
        
        Args:
            context: Contains task and resource matching data
        
        Returns:
            Cost analysis and optimization recommendations
        """
        self.log("Starting cost optimization...")
        
        # Get classified tasks
        task_classification = context.get('TaskClassificationAgent', {})
        tasks = task_classification.get('classified_tasks', [])
        
        # Get resource recommendations
        resource_matching = context.get('ResourceMatchingAgent', {})
        task_recommendations = resource_matching.get('task_recommendations', [])
        
        if not tasks or not task_recommendations:
            self.log("Insufficient data for cost optimization")
            return {
                "cost_analysis": {},
                "status": "insufficient_data"
            }
        
        # Analyze costs for each task
        task_cost_analysis = []
        total_cost_estimates = []
        
        for i, task in enumerate(tasks):
            if i < len(task_recommendations):
                recommendations = task_recommendations[i]
                cost_analysis = self.analyze_task_costs(task, recommendations)
                task_cost_analysis.append(cost_analysis)
                
                # Track total estimates
                if cost_analysis.get('cost_recommendations'):
                    total_cost_estimates.append(cost_analysis['cost_recommendations'][0].get('total_cost', 0))
        
        # Generate overall cost summary
        cost_summary = self.generate_cost_summary(task_cost_analysis, total_cost_estimates)
        
        return {
            "task_cost_analysis": task_cost_analysis,
            "cost_summary": cost_summary,
            "total_estimated_cost": cost_summary.get('total_estimated_cost', 0),
            "cost_optimization_potential": cost_summary.get('optimization_potential', 0),
            "status": "success"
        }
    
    def analyze_task_costs(self, task: Dict, recommendations: Dict) -> Dict:
        """Analyze costs for a single task"""
        
        task_name = task.get('task_name', '')
        estimated_effort = task.get('estimated_effort', 8)
        matched_resources = recommendations.get('matched_resources', [])
        
        if not matched_resources:
            return {
                "task_name": task_name,
                "estimated_effort": estimated_effort,
                "cost_recommendations": [],
                "message": "No resources matched"
            }
        
        # Calculate costs for top matches (limit to 5 for efficiency)
        cost_recommendations = []
        
        for resource in matched_resources[:5]:
            resource_id = resource.get('resource_id', resource.get('id'))
            resource_type = resource.get('type', 'human')
            
            # Call Cost MCP server
            cost_response = self.call_mcp_tool(
                'cost',
                'estimate_assignment_cost',
                {
                    'resource_id': resource_id,
                    'resource_type': resource_type,
                    'estimated_effort': estimated_effort
                }
            )
            
            if cost_response.get('success'):
                cost_data = cost_response.get('result', {})
                cost_recommendations.append({
                    "resource_name": resource.get('name', cost_data.get('resource_name')),
                    "resource_type": resource_type,
                    "skill_match_score": resource.get('match_score', 0),
                    "total_cost": cost_data.get('total_cost', 0),
                    "cost_per_hour": cost_data.get('cost_per_hour', 0),
                    "quality_score": cost_data.get('quality_score', 0),
                    "cost_efficiency_score": cost_data.get('cost_efficiency_score', 0)
                })
        
        # Sort by cost efficiency
        cost_recommendations.sort(key=lambda x: x['cost_efficiency_score'], reverse=True)
        
        # Identify cost-optimal choice
        if cost_recommendations:
            best_value = cost_recommendations[0]
            cheapest = min(cost_recommendations, key=lambda x: x['total_cost'])
            
            return {
                "task_name": task_name,
                "estimated_effort": estimated_effort,
                "cost_recommendations": cost_recommendations,
                "best_value": best_value,
                "cheapest_option": cheapest,
                "cost_range": {
                    "min": cheapest['total_cost'],
                    "max": cost_recommendations[-1]['total_cost'],
                    "savings_potential": cost_recommendations[-1]['total_cost'] - cheapest['total_cost']
                }
            }
        else:
            return {
                "task_name": task_name,
                "estimated_effort": estimated_effort,
                "cost_recommendations": [],
                "message": "Cost estimation failed"
            }
    
    def generate_cost_summary(self, task_analyses: List[Dict], total_estimates: List[float]) -> Dict:
        """Generate overall cost summary"""
        
        total_cost = sum(total_estimates)
        
        # Calculate potential savings
        total_savings_potential = sum(
            analysis.get('cost_range', {}).get('savings_potential', 0)
            for analysis in task_analyses
        )
        
        # Count AI vs Human recommendations
        ai_recommendations = 0
        human_recommendations = 0
        
        for analysis in task_analyses:
            best = analysis.get('best_value', {})
            if best.get('resource_type') == 'ai':
                ai_recommendations += 1
            else:
                human_recommendations += 1
        
        return {
            "total_estimated_cost": round(total_cost, 2),
            "optimization_potential": round(total_savings_potential, 2),
            "optimization_percentage": round((total_savings_potential / total_cost * 100) if total_cost > 0 else 0, 2),
            "ai_recommendations": ai_recommendations,
            "human_recommendations": human_recommendations,
            "average_cost_per_task": round(total_cost / len(task_analyses) if task_analyses else 0, 2),
            "cost_efficiency_message": f"Potential savings of ${round(total_savings_potential, 2)} by choosing cost-optimal resources"
        }
