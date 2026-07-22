"""
Workload Optimization Agent - Agent 6
Analyzes resource workload and suggests optimized assignments
"""
from agents import Agent
from typing import Dict, Any, List

class WorkloadOptimizationAgent(Agent):
    """
    Optimizes resource assignments based on current workload.
    This agent runs in parallel with agents 5, 7-9. No LLM call - uses MCP tools.
    """
    
    def __init__(self):
        super().__init__(
            name="WorkloadOptimizationAgent",
            description="Optimizes workload distribution across resources"
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze workload and provide optimization recommendations
        
        Args:
            context: Contains 'TaskClassificationAgent' and 'ResourceMatchingAgent' results
        
        Returns:
            Workload optimization recommendations
        """
        self.log("Starting workload optimization...")
        
        # Get current workload from MCP server
        workload_response = self.call_mcp_tool('resource', 'get_current_workload')
        
        if not workload_response.get('success'):
            self.log("Failed to get workload data")
            return {
                "workload_analysis": {},
                "status": "error"
            }
        
        workload_data = workload_response.get('result', [])
        
        # Get capacity metrics
        capacity_response = self.call_mcp_tool('resource', 'get_resource_capacity')
        capacity_data = capacity_response.get('result', {}) if capacity_response.get('success') else {}
        
        # Get utilization metrics from Analytics
        utilization_response = self.call_mcp_tool('analytics', 'generate_utilization_metrics')
        utilization_data = utilization_response.get('result', {}) if utilization_response.get('success') else {}
        
        # Analyze workload distribution
        analysis = self.analyze_workload(workload_data, capacity_data, utilization_data)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(analysis, context)
        
        return {
            "workload_analysis": analysis,
            "optimization_recommendations": recommendations,
            "status": "success"
        }
    
    def analyze_workload(self, workload_data: List[Dict], capacity_data: Dict, utilization_data: Dict) -> Dict:
        """Analyze current workload distribution"""
        
        overloaded = []
        underutilized = []
        balanced = []
        
        for resource in workload_data:
            workload = resource.get('current_workload', 0)
            resource_info = {
                "id": resource.get('id'),
                "name": resource.get('name'),
                "role": resource.get('role'),
                "current_workload": workload,
                "availability": resource.get('availability')
            }
            
            if workload > 80:
                overloaded.append(resource_info)
            elif workload < 30:
                underutilized.append(resource_info)
            else:
                balanced.append(resource_info)
        
        return {
            "overloaded_resources": overloaded,
            "underutilized_resources": underutilized,
            "balanced_resources": balanced,
            "overload_count": len(overloaded),
            "underutilized_count": len(underutilized),
            "capacity_metrics": capacity_data,
            "utilization_metrics": utilization_data
        }
    
    def generate_recommendations(self, analysis: Dict, context: Dict) -> List[Dict]:
        """Generate workload optimization recommendations"""
        
        recommendations = []
        
        overloaded = analysis.get('overloaded_resources', [])
        underutilized = analysis.get('underutilized_resources', [])
        
        # Recommend redistributing work from overloaded to underutilized
        if overloaded and underutilized:
            recommendations.append({
                "type": "workload_redistribution",
                "priority": "High",
                "message": f"{len(overloaded)} resources are overloaded (>80% capacity). Consider redistributing to {len(underutilized)} underutilized resources.",
                "overloaded_resources": [r['name'] for r in overloaded[:3]],
                "alternative_resources": [r['name'] for r in underutilized[:3]]
            })
        
        # Recommend AI agents for simple tasks to free up human resources
        task_classification = context.get('TaskClassificationAgent', {})
        classified_tasks = task_classification.get('classified_tasks', [])
        low_complexity_count = len([t for t in classified_tasks if t.get('complexity') == 'Low'])
        
        if low_complexity_count > 0 and overloaded:
            recommendations.append({
                "type": "ai_agent_delegation",
                "priority": "Medium",
                "message": f"{low_complexity_count} low-complexity tasks could be assigned to AI agents to reduce human workload.",
                "estimated_savings": f"~{low_complexity_count * 8} hours"
            })
        
        # Warn about underutilization
        if len(underutilized) > 3:
            recommendations.append({
                "type": "underutilization_alert",
                "priority": "Low",
                "message": f"{len(underutilized)} resources are underutilized (<30% capacity). Consider assigning more work.",
                "underutilized_resources": [r['name'] for r in underutilized[:5]]
            })
        
        return recommendations
