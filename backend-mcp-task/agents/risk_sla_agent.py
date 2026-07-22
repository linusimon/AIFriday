"""
Risk and SLA Agent - Agent 8
Predicts SLA breach risks and quality risks
"""
from agents import Agent
from typing import Dict, Any, List

class RiskSLAAgent(Agent):
    """
    Predicts SLA breach risks and quality risks for assignments.
    This agent runs in parallel with agents 5-7, 9. No LLM call - uses MCP tools.
    """
    
    def __init__(self):
        super().__init__(
            name="RiskSLAAgent",
            description="Predicts SLA breach risks and quality risks"
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze SLA compliance and risks
        
        Args:
            context: Contains task and resource data
        
        Returns:
            Risk assessment and SLA predictions
        """
        self.log("Starting risk and SLA analysis...")
        
        # Get classified tasks
        task_classification = context.get('TaskClassificationAgent', {})
        tasks = task_classification.get('classified_tasks', [])
        
        # Get resource recommendations
        resource_matching = context.get('ResourceMatchingAgent', {})
        task_recommendations = resource_matching.get('task_recommendations', [])
        
        if not tasks:
            self.log("No tasks to analyze")
            return {
                "risk_analysis": [],
                "status": "no_data"
            }
        
        # Analyze risks for each task
        risk_analyses = []
        
        for i, task in enumerate(tasks):
            risk_analysis = self.analyze_task_risk(task, i, task_recommendations)
            risk_analyses.append(risk_analysis)
        
        # Generate overall risk summary
        risk_summary = self.generate_risk_summary(risk_analyses)
        
        return {
            "task_risk_analyses": risk_analyses,
            "risk_summary": risk_summary,
            "high_risk_count": risk_summary.get('high_risk_count', 0),
            "status": "success"
        }
    
    def analyze_task_risk(self, task: Dict, task_index: int, all_recommendations: List[Dict]) -> Dict:
        """Analyze risk for a single task"""
        
        task_name = task.get('task_name', '')
        priority = task.get('priority', 'Medium')
        complexity = task.get('complexity', 'Medium')
        estimated_effort = task.get('estimated_effort', 8)
        
        # Get SLA requirements
        sla_response = self.call_mcp_tool(
            'sla',
            'get_sla_requirements',
            {'category': priority}
        )
        
        sla_rules = []
        if sla_response.get('success'):
            sla_rules = sla_response.get('result', [])
        
        # Predict breach risk
        breach_risk_response = self.call_mcp_tool(
            'sla',
            'predict_breach_risk',
            {
                'task_id': task.get('task_id', task_index + 1),
                'estimated_effort': estimated_effort
            }
        )
        
        breach_risk = {}
        if breach_risk_response.get('success'):
            breach_risk = breach_risk_response.get('result', {})
        
        # Analyze quality risk based on resource matches
        quality_risk = self.assess_quality_risk(task, task_index, all_recommendations)
        
        # Calculate overall risk score
        risk_score = self.calculate_risk_score(breach_risk, quality_risk, complexity, priority)
        
        return {
            "task_name": task_name,
            "task_id": task.get('task_id', task_index + 1),
            "priority": priority,
            "complexity": complexity,
            "estimated_effort": estimated_effort,
            "sla_requirements": sla_rules[0] if sla_rules else {},
            "breach_risk": breach_risk,
            "quality_risk": quality_risk,
            "overall_risk_score": risk_score,
            "overall_risk_level": self.get_risk_level(risk_score),
            "mitigation_recommendations": self.generate_mitigation_recommendations(risk_score, breach_risk, quality_risk)
        }
    
    def assess_quality_risk(self, task: Dict, task_index: int, all_recommendations: List[Dict]) -> Dict:
        """Assess quality risk based on available resources"""
        
        if task_index < len(all_recommendations):
            recommendations = all_recommendations[task_index]
            matched_resources = recommendations.get('matched_resources', [])
            
            if not matched_resources:
                return {
                    "risk_level": "High",
                    "reason": "No suitable resources found",
                    "score": 80
                }
            
            # Check best match quality
            best_match = matched_resources[0]
            match_score = best_match.get('match_score', 0)
            quality_score = best_match.get('quality_score', 0)
            
            if match_score < 50:
                return {
                    "risk_level": "High",
                    "reason": f"Low skill match ({match_score}%)",
                    "score": 70
                }
            elif quality_score < 80:
                return {
                    "risk_level": "Medium",
                    "reason": f"Moderate quality score ({quality_score})",
                    "score": 50
                }
            else:
                return {
                    "risk_level": "Low",
                    "reason": f"Good match ({match_score}%) with high quality ({quality_score})",
                    "score": 20
                }
        
        return {
            "risk_level": "Unknown",
            "reason": "No resource recommendations available",
            "score": 50
        }
    
    def calculate_risk_score(self, breach_risk: Dict, quality_risk: Dict, complexity: str, priority: str) -> int:
        """Calculate overall risk score (0-100, higher = more risk)"""
        
        # Base score from SLA breach risk
        breach_score = 0
        breach_level = breach_risk.get('risk_level', 'Low')
        if breach_level == 'High':
            breach_score = 40
        elif breach_level == 'Medium':
            breach_score = 20
        else:
            breach_score = 5
        
        # Quality risk score
        quality_score = quality_risk.get('score', 30)
        
        # Complexity multiplier
        complexity_weight = {'High': 1.3, 'Medium': 1.0, 'Low': 0.7}.get(complexity, 1.0)
        
        # Priority weight
        priority_weight = {'Critical': 1.4, 'High': 1.2, 'Medium': 1.0, 'Low': 0.8}.get(priority, 1.0)
        
        # Calculate weighted score
        overall_score = ((breach_score * 0.4 + quality_score * 0.6) * complexity_weight * priority_weight)
        
        return min(100, int(overall_score))
    
    def get_risk_level(self, risk_score: int) -> str:
        """Convert risk score to risk level"""
        if risk_score >= 70:
            return "High"
        elif risk_score >= 40:
            return "Medium"
        else:
            return "Low"
    
    def generate_mitigation_recommendations(self, risk_score: int, breach_risk: Dict, quality_risk: Dict) -> List[str]:
        """Generate recommendations to mitigate risks"""
        recommendations = []
        
        if risk_score >= 70:
            recommendations.append("HIGH PRIORITY: This task requires immediate attention and senior resource assignment")
        
        if breach_risk.get('risk_level') == 'High':
            recommendations.append(f"SLA breach risk detected. {breach_risk.get('escalation_rule', 'Escalate to management')}")
        
        if quality_risk.get('risk_level') == 'High':
            recommendations.append(f"Quality risk: {quality_risk.get('reason')}. Consider alternative resources or providing additional support")
        
        if not recommendations:
            recommendations.append("Risk is within acceptable levels. Proceed with recommended assignment")
        
        return recommendations
    
    def generate_risk_summary(self, risk_analyses: List[Dict]) -> Dict:
        """Generate overall risk summary"""
        
        total_tasks = len(risk_analyses)
        high_risk = len([r for r in risk_analyses if r.get('overall_risk_level') == 'High'])
        medium_risk = len([r for r in risk_analyses if r.get('overall_risk_level') == 'Medium'])
        low_risk = len([r for r in risk_analyses if r.get('overall_risk_level') == 'Low'])
        
        sla_breach_risks = len([r for r in risk_analyses if r.get('breach_risk', {}).get('risk_level') == 'High'])
        quality_risks = len([r for r in risk_analyses if r.get('quality_risk', {}).get('risk_level') == 'High'])
        
        return {
            "total_tasks": total_tasks,
            "high_risk_count": high_risk,
            "medium_risk_count": medium_risk,
            "low_risk_count": low_risk,
            "sla_breach_risks": sla_breach_risks,
            "quality_risks": quality_risks,
            "risk_distribution": {
                "High": high_risk,
                "Medium": medium_risk,
                "Low": low_risk
            },
            "overall_assessment": "Critical" if high_risk > total_tasks * 0.3 else "Moderate" if high_risk > 0 else "Low"
        }
