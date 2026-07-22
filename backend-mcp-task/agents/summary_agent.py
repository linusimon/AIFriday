"""
Summary Agent - Agent 10
Generates executive summary and final user-facing report
"""
from agents import Agent
from typing import Dict, Any, List
import json

class SummaryAgent(Agent):
    """
    Generates comprehensive summary and final report.
    This is the final agent in the pipeline (LLM Call 6).
    """
    
    def __init__(self):
        super().__init__(
            name="SummaryAgent",
            description="Generates executive summary and detailed report"
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate final summary report
        
        Args:
            context: Contains outputs from all agents
        
        Returns:
            Executive summary and detailed report
        """
        self.log("Generating final summary...")
        
        # Get all relevant data
        doc_analysis = context.get('DocumentAnalysisAgent', {})
        classification = context.get('TaskClassificationAgent', {})
        decisions = context.get('DecisionAgent', {})
        cost_optimization = context.get('CostOptimizationAgent', {})
        risk_sla = context.get('RiskSLAAgent', {})
        workload_optimization = context.get('WorkloadOptimizationAgent', {})
        
        # Generate executive summary using LLM
        executive_summary = self.generate_executive_summary(context)
        
        # Generate detailed recommendations
        detailed_recommendations = self.generate_detailed_recommendations(context)
        
        # Compile final report
        final_report = {
            "executive_summary": executive_summary,
            "analysis_overview": {
                "total_tasks": len(decisions.get('final_decisions', [])),
                "total_estimated_effort": classification.get('classification_summary', {}).get('total_estimated_effort', 0),
                "total_estimated_cost": cost_optimization.get('total_estimated_cost', 0),
                "high_risk_tasks": risk_sla.get('high_risk_count', 0),
                "ai_assignments": decisions.get('decision_summary', {}).get('ai_assignments', 0),
                "human_assignments": decisions.get('decision_summary', {}).get('human_assignments', 0)
            },
            "task_assignments": decisions.get('final_decisions', []),
            "cost_analysis": {
                "total_cost": cost_optimization.get('total_estimated_cost', 0),
                "optimization_potential": cost_optimization.get('cost_optimization_potential', 0),
                "cost_summary": cost_optimization.get('cost_summary', {})
            },
            "risk_assessment": {
                "overall_risk": risk_sla.get('risk_summary', {}).get('overall_assessment', 'Unknown'),
                "high_risk_count": risk_sla.get('high_risk_count', 0),
                "risk_distribution": risk_sla.get('risk_summary', {}).get('risk_distribution', {})
            },
            "workload_insights": {
                "overloaded_resources": len(workload_optimization.get('workload_analysis', {}).get('overloaded_resources', [])),
                "underutilized_resources": len(workload_optimization.get('workload_analysis', {}).get('underutilized_resources', [])),
                "recommendations": workload_optimization.get('optimization_recommendations', [])
            },
            "detailed_recommendations": detailed_recommendations,
            "next_steps": self.generate_next_steps(context)
        }
        
        self.log("Summary generation complete")
        
        return {
            "final_report": final_report,
            "status": "success"
        }
    
    def generate_executive_summary(self, context: Dict[str, Any]) -> str:
        """Generate executive summary using LLM"""
        
        decisions = context.get('DecisionAgent', {})
        cost_optimization = context.get('CostOptimizationAgent', {})
        risk_sla = context.get('RiskSLAAgent', {})
        workload_optimization = context.get('WorkloadOptimizationAgent', {})
        classification = context.get('TaskClassificationAgent', {})
        
        # Prepare summary data
        summary_data = {
            "total_tasks": len(decisions.get('final_decisions', [])),
            "complexity_distribution": classification.get('classification_summary', {}).get('complexity_distribution', {}),
            "ai_vs_human": decisions.get('decision_summary', {}).get('assignment_distribution', {}),
            "total_cost": cost_optimization.get('total_estimated_cost', 0),
            "cost_savings_potential": cost_optimization.get('cost_optimization_potential', 0),
            "overall_risk": risk_sla.get('risk_summary', {}).get('overall_assessment', 'Unknown'),
            "high_risk_count": risk_sla.get('high_risk_count', 0),
            "workload_status": {
                "overloaded": len(workload_optimization.get('workload_analysis', {}).get('overloaded_resources', [])),
                "underutilized": len(workload_optimization.get('workload_analysis', {}).get('underutilized_resources', []))
            }
        }
        
        system_prompt = """You are an executive report writer. Create a concise, professional executive summary for a task routing analysis.

The summary should:
1. Highlight key findings and metrics
2. Identify critical risks and opportunities
3. Provide actionable insights
4. Be written for business stakeholders (non-technical)
5. Be 3-5 paragraphs maximum

Focus on business value, cost efficiency, risk management, and resource optimization."""
        
        context_json = json.dumps(summary_data, indent=2)
        user_message = f"""Generate an executive summary for this task routing analysis:

{context_json}

Write a clear, professional summary highlighting the key insights and recommendations."""
        
        # Call LLM
        llm_response = self.call_llm(system_prompt, user_message, temperature=0.5)
        
        return llm_response if llm_response and not llm_response.startswith('Error:') else self.fallback_executive_summary(summary_data)
    
    def fallback_executive_summary(self, data: Dict) -> str:
        """Generate basic executive summary without LLM"""
        total_tasks = data.get('total_tasks', 0)
        total_cost = data.get('total_cost', 0)
        ai_count = data.get('ai_vs_human', {}).get('AI', 0)
        human_count = data.get('ai_vs_human', {}).get('Human', 0)
        high_risk = data.get('high_risk_count', 0)
        
        return f"""EXECUTIVE SUMMARY

The intelligent task routing system has analyzed {total_tasks} tasks and generated optimal resource assignments. 

RESOURCE ALLOCATION: {human_count} tasks are recommended for human resources and {ai_count} tasks for AI agents, balancing quality requirements with cost efficiency. The total estimated project cost is ${total_cost:.2f}.

RISK ASSESSMENT: {high_risk} tasks have been identified as high-risk, requiring priority attention and senior resource assignment. The overall risk assessment is {data.get('overall_risk', 'Unknown')}.

RECOMMENDATIONS: Immediate action is recommended for high-priority tasks. Cost optimization opportunities of ${data.get('cost_savings_potential', 0):.2f} have been identified through strategic resource allocation."""
    
    def generate_detailed_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """Generate detailed actionable recommendations as a list of strings matching frontend schema"""
        
        recommendations = []
        
        # Decision-based recommendations
        decisions = context.get('DecisionAgent', {})
        final_decisions = decisions.get('final_decisions', [])
        
        # High-priority tasks
        high_priority_tasks = [d for d in final_decisions if d.get('priority') in ['Critical', 'High']]
        if high_priority_tasks:
            recommendations.append(
                f"Critical Task Priority: Assign critical tasks immediately. Recommended path: " +
                "; ".join([f"assign '{t.get('task_name')}' to {t.get('recommended_resource', {}).get('name')}" for t in high_priority_tasks[:3]])
            )
        
        # Risk-based recommendations
        risk_sla = context.get('RiskSLAAgent', {})
        high_risk_tasks = [r for r in risk_sla.get('task_risk_analyses', []) if r.get('overall_risk_level') == 'High']
        if high_risk_tasks:
            recommendations.append(
                f"Risk Management: {len(high_risk_tasks)} tasks have high SLA or quality risk. " +
                "Mitigation: Implement daily status updates and prioritize senior peer reviews."
            )
        
        # Cost optimization recommendations
        cost_optimization = context.get('CostOptimizationAgent', {})
        cost_savings = cost_optimization.get('cost_optimization_potential', 0)
        if cost_savings > 0:
            recommendations.append(
                f"Cost Optimization: Potential savings of ${cost_savings:.2f} identified. " +
                "Action: Leverage specialized AI agents (e.g. MobileUX AI or TestGen AI) for lower-complexity tasks."
            )
        
        # Workload recommendations
        workload_optimization = context.get('WorkloadOptimizationAgent', {})
        workload_recs = workload_optimization.get('optimization_recommendations', [])
        if workload_recs:
            for rec in workload_recs[:2]:
                recommendations.append(f"Resource Workload: {rec.get('message', '')}")
                
        if not recommendations:
            recommendations.append("All tasks routed optimally. Monitor resource utilization to ensure balanced workload.")
        
        return recommendations
    
    def generate_next_steps(self, context: Dict[str, Any]) -> List[str]:
        """Generate actionable next steps"""
        
        next_steps = []
        
        decisions = context.get('DecisionAgent', {})
        risk_sla = context.get('RiskSLAAgent', {})
        
        # Step 1: Review and approve assignments
        next_steps.append("Review and approve the recommended task assignments")
        
        # Step 2: Address high-risk tasks
        high_risk_count = risk_sla.get('high_risk_count', 0)
        if high_risk_count > 0:
            next_steps.append(f"Prioritize {high_risk_count} high-risk tasks for immediate assignment and monitoring")
        
        # Step 3: Assign resources
        next_steps.append("Assign tasks to recommended resources through your project management system")
        
        # Step 4: Set up monitoring
        next_steps.append("Set up progress monitoring and SLA tracking for all assignments")
        
        # Step 5: Review workload
        next_steps.append("Review workload distribution and adjust as needed to prevent resource overload")
        
        return next_steps
