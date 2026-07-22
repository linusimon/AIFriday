"""
Decision Agent - Agent 9
Consolidates all agent outputs and generates final assignment recommendations
"""
from agents import Agent
from typing import Dict, Any, List
import json

class DecisionAgent(Agent):
    """
    Consolidates outputs from all agents and makes final routing decisions.
    This is the 9th agent in the pipeline (LLM Call 5).
    """
    
    def __init__(self):
        super().__init__(
            name="DecisionAgent",
            description="Makes final routing decisions based on all agent outputs"
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate final assignment recommendations
        
        Args:
            context: Contains outputs from all previous agents
        
        Returns:
            Final routing decisions
        """
        self.log("Starting decision making...")
        
        # Get data from all previous agents
        tasks = context.get('TaskClassificationAgent', {}).get('classified_tasks', [])
        resource_matching = context.get('ResourceMatchingAgent', {})
        workload_optimization = context.get('WorkloadOptimizationAgent', {})
        cost_optimization = context.get('CostOptimizationAgent', {})
        risk_sla = context.get('RiskSLAAgent', {})
        
        if not tasks:
            self.log("No tasks to make decisions on")
            return {
                "final_decisions": [],
                "status": "no_data"
            }
        
        # Generate decisions for each task
        final_decisions = []
        
        for i, task in enumerate(tasks):
            self.log(f"Making decision for task {i+1}/{len(tasks)}: {task.get('task_name')}")
            decision = self.make_task_decision(task, i, context)
            final_decisions.append(decision)
        
        # Generate executive decision summary
        decision_summary = self.generate_decision_summary(final_decisions)
        
        return {
            "final_decisions": final_decisions,
            "decision_summary": decision_summary,
            "total_decisions": len(final_decisions),
            "status": "success"
        }
    
    def make_task_decision(self, task: Dict, task_index: int, context: Dict) -> Dict:
        """Make routing decision for a single task using LLM"""
        
        # Gather all relevant data for this task
        task_data = {
            "task_name": task.get('task_name'),
            "description": task.get('description'),
            "complexity": task.get('complexity'),
            "priority": task.get('priority'),
            "estimated_effort": task.get('estimated_effort'),
            "skills_required": task.get('skills_required'),
            "category": task.get('category')
        }
        
        task_name = task.get('task_name')
        
        # Get resource recommendations
        resource_matching = context.get('ResourceMatchingAgent', {})
        task_recommendations = resource_matching.get('task_recommendations', [])
        matched_rec = next((r for r in task_recommendations if r.get('task_name') == task_name), None)
        resource_options = matched_rec.get('matched_resources', [])[:5] if matched_rec else []
        
        # Get cost analysis
        cost_optimization = context.get('CostOptimizationAgent', {})
        task_cost_analyses = cost_optimization.get('task_cost_analysis', [])
        cost_data = next((c for c in task_cost_analyses if c.get('task_name') == task_name), {})
        
        # Get risk analysis
        risk_sla = context.get('RiskSLAAgent', {})
        task_risk_analyses = risk_sla.get('task_risk_analyses', [])
        risk_data = next((r for r in task_risk_analyses if r.get('task_name') == task_name), {})
        
        # Get workload insights
        workload_optimization = context.get('WorkloadOptimizationAgent', {})
        workload_analysis = workload_optimization.get('workload_analysis', {})
        
        # Use LLM to make final decision
        system_prompt = """You are an intelligent task routing decision maker. You must analyze all available data and recommend the BEST resource assignment for a task.

Consider:
1. Skill match quality (higher is better)
2. Resource availability and workload
3. Cost efficiency (balance cost vs quality)
4. Risk factors (SLA, quality risks)
5. Priority and complexity

Your decision should BALANCE all factors, not just optimize for one. Critical tasks should prioritize quality and SLA compliance over cost.

Return a JSON object with:
- recommended_resource_name: Name of the recommended resource
- recommended_resource_type: "human" or "ai"
- recommended_resource_id: ID of the resource
- confidence_score: 0-100 confidence in this decision
- reasoning: Detailed explanation of why this resource is recommended
- alternative_resource: Name of second-best option
- key_factors: List of key factors that influenced the decision"""
        
        # Prepare decision context
        decision_context = json.dumps({
            "task": task_data,
            "resource_options": resource_options,
            "cost_analysis": {
                "best_value": cost_data.get('best_value', {}),
                "cheapest": cost_data.get('cheapest_option', {}),
                "cost_range": cost_data.get('cost_range', {})
            },
            "risk_analysis": {
                "overall_risk_level": risk_data.get('overall_risk_level', 'Unknown'),
                "breach_risk": risk_data.get('breach_risk', {}),
                "quality_risk": risk_data.get('quality_risk', {}),
                "mitigation_recommendations": risk_data.get('mitigation_recommendations', [])
            },
            "workload_context": {
                "overloaded_count": workload_analysis.get('overload_count', 0),
                "underutilized_count": workload_analysis.get('underutilized_count', 0)
            }
        }, indent=2)
        
        user_message = f"""Make the optimal routing decision for this task:

{decision_context}

Select the BEST resource considering all factors. Critical and High priority tasks should prioritize quality and SLA compliance."""
        
        # Call LLM
        llm_response = self.call_llm(system_prompt, user_message, temperature=0.4, response_format='json')
        
        try:
            decision = json.loads(llm_response)
            
            skills_raw = task.get('skills_required', '')
            if isinstance(skills_raw, list):
                skills_list = [str(s).strip() for s in skills_raw if str(s).strip()]
            elif isinstance(skills_raw, str):
                skills_list = [s.strip() for s in skills_raw.split(',') if s.strip()]
            else:
                skills_list = []
            
            frontend_resource_options = []
            for r in resource_options:
                frontend_resource_options.append({
                    "resource_id": r.get('resource_id', r.get('id', 0)),
                    "resource_name": r.get('name', 'Unknown'),
                    "resource_type": r.get('type', 'human'),
                    "match_score": r.get('match_score', 0),
                    "skill_match": r.get('skill_match', []),
                    "missing_skills": r.get('missing_skills', []),
                    "availability": r.get('availability', 'Available'),
                    "current_workload": r.get('current_workload', 0),
                    "cost_per_hour": r.get('cost_per_hour', 0.0),
                    "estimated_cost": r.get('estimated_cost', 0.0),
                    "quality_score": r.get('quality_score', 0),
                    "sla_compliance": r.get('sla_compliance', 0),
                    "risk_level": r.get('risk_level', 'Low')
                })
                
            # Safe parsing of resource_id and confidence_score
            try:
                res_id = int(decision.get('recommended_resource_id', 0) or 0)
            except (ValueError, TypeError):
                res_id = 0
                
            try:
                raw_conf = decision.get('confidence_score', 80)
                if isinstance(raw_conf, str) and '%' in raw_conf:
                    raw_conf = raw_conf.replace('%', '')
                confidence_score = int(raw_conf or 80)
            except (ValueError, TypeError):
                confidence_score = 80
                
            recommended_cost = cost_data.get('best_value', {}).get('total_cost', 0.0)
            
            return {
                "task_id": task.get('task_id', task_index + 1),
                "task_name": task.get('task_name'),
                "task_description": task.get('description', ''),
                "complexity": task.get('complexity', 'Medium'),
                "estimated_effort": task.get('estimated_effort', 8),
                "skills_required": skills_list,
                "recommended_resource": {
                    "resource_id": res_id,
                    "name": decision.get('recommended_resource_name', 'Unknown'),
                    "type": decision.get('recommended_resource_type', 'human'),
                    "confidence_score": confidence_score,
                    "reasoning": decision.get('reasoning', '')
                },
                "resource_options": frontend_resource_options,
                "cost_analysis": {
                    "recommended_cost": recommended_cost,
                    "cheapest_cost": cost_data.get('cheapest_option', {}).get('total_cost', recommended_cost),
                    "premium_cost": cost_data.get('premium_option', {}).get('total_cost', recommended_cost),
                    "potential_savings": cost_data.get('potential_savings', 0.0)
                },
                "risk_assessment": {
                    "risk_level": risk_data.get('overall_risk_level', 'Low'),
                    "risk_factors": risk_data.get('risk_factors', []),
                    "mitigation_strategies": risk_data.get('mitigation_recommendations', [])
                },
                "sla_compliance": {
                    "expected_completion": "2026-07-18",
                    "sla_breach_risk": risk_data.get('breach_risk', {}).get('breach_probability', 10.0)
                }
            }
        
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse LLM decision: {str(e)}")
            # Fallback: use simple logic
            return self.fallback_decision(task, task_index, resource_options, cost_data, risk_data)
    
    def fallback_decision(self, task: Dict, task_index: int, resource_options: List, cost_data: Dict, risk_data: Dict) -> Dict:
        """Simple fallback decision logic matching frontend schema"""
        best_resource = resource_options[0] if resource_options else {}
        
        skills_raw = task.get('skills_required', '')
        if isinstance(skills_raw, list):
            skills_list = [str(s).strip() for s in skills_raw if str(s).strip()]
        elif isinstance(skills_raw, str):
            skills_list = [s.strip() for s in skills_raw.split(',') if s.strip()]
        else:
            skills_list = []
        
        frontend_resource_options = []
        for r in resource_options:
            frontend_resource_options.append({
                "resource_id": r.get('resource_id', r.get('id', 0)),
                "resource_name": r.get('name', 'Unknown'),
                "resource_type": r.get('type', 'human'),
                "match_score": r.get('match_score', 0),
                "skill_match": r.get('skill_match', []),
                "missing_skills": r.get('missing_skills', []),
                "availability": r.get('availability', 'Available'),
                "current_workload": r.get('current_workload', 0),
                "cost_per_hour": r.get('cost_per_hour', 0.0),
                "estimated_cost": r.get('estimated_cost', 0.0),
                "quality_score": r.get('quality_score', 0),
                "sla_compliance": r.get('sla_compliance', 0),
                "risk_level": r.get('risk_level', 'Low')
            })
            
        recommended_cost = cost_data.get('best_value', {}).get('total_cost', 0.0)
        if recommended_cost == 0.0 and best_resource:
            recommended_cost = best_resource.get('cost_per_hour', 50) * task.get('estimated_effort', 8)
            
        return {
            "task_name": task.get('task_name'),
            "task_description": task.get('description', ''),
            "complexity": task.get('complexity', 'Medium'),
            "estimated_effort": task.get('estimated_effort', 8),
            "skills_required": skills_list,
            "recommended_resource": {
                "resource_id": best_resource.get('resource_id', 0),
                "name": best_resource.get('name', 'Unknown'),
                "type": best_resource.get('type', 'human'),
                "confidence_score": 60,
                "reasoning": "Fallback decision based on skill match"
            },
            "resource_options": frontend_resource_options,
            "cost_analysis": {
                "recommended_cost": recommended_cost,
                "cheapest_cost": cost_data.get('cheapest_option', {}).get('total_cost', recommended_cost),
                "premium_cost": cost_data.get('premium_option', {}).get('total_cost', recommended_cost),
                "potential_savings": cost_data.get('potential_savings', 0.0)
            },
            "risk_assessment": {
                "risk_level": risk_data.get('overall_risk_level', 'Low'),
                "risk_factors": risk_data.get('risk_factors', []),
                "mitigation_strategies": risk_data.get('mitigation_recommendations', [])
            },
            "sla_compliance": {
                "expected_completion": "2026-07-18",
                "sla_breach_risk": risk_data.get('breach_risk', {}).get('breach_probability', 10.0)
            }
        }
    
    def generate_decision_summary(self, decisions: List[Dict]) -> Dict:
        """Generate summary of all decisions"""
        
        total = len(decisions)
        ai_assignments = len([d for d in decisions if d.get('recommended_resource', {}).get('type') == 'ai'])
        human_assignments = total - ai_assignments
        
        high_confidence = len([d for d in decisions if d.get('recommended_resource', {}).get('confidence_score', 0) >= 80])
        medium_confidence = len([d for d in decisions if 60 <= d.get('recommended_resource', {}).get('confidence_score', 0) < 80])
        low_confidence = len([d for d in decisions if d.get('recommended_resource', {}).get('confidence_score', 0) < 60])
        
        high_risk_assignments = len([d for d in decisions if d.get('risk_assessment', {}).get('risk_level') == 'High'])
        
        total_cost = sum([d.get('cost_analysis', {}).get('recommended_cost', 0) for d in decisions])
        
        return {
            "total_tasks": total,
            "ai_assignments": ai_assignments,
            "human_assignments": human_assignments,
            "assignment_distribution": {
                "AI": ai_assignments,
                "Human": human_assignments
            },
            "confidence_distribution": {
                "High (≥80)": high_confidence,
                "Medium (60-79)": medium_confidence,
                "Low (<60)": low_confidence
            },
            "high_risk_assignments": high_risk_assignments,
            "total_estimated_cost": round(total_cost, 2),
            "average_confidence": round(sum([d.get('recommended_resource', {}).get('confidence_score', 0) for d in decisions]) / total if total > 0 else 0, 2)
        }
