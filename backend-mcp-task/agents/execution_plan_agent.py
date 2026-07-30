"""
Project Execution Agent for generating Agile User Stories, Resource Assignments, Effort/Cost Estimations, and Sprint Timelines.
"""
from agents import Agent
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta
import database

class ProjectExecutionAgent(Agent):
    """
    Generates a full Agile Project Execution Plan including:
    - Detailed User Stories with acceptance criteria
    - Optimal Human Resource / AI Agent assignments
    - Story Points (Fibonacci), Effort Hours & Cost Estimations
    - Multi-Sprint Timeline Roadmap with Milestones
    """
    
    def __init__(self):
        super().__init__(
            name="ProjectExecutionAgent",
            description="Generates Agile User Stories, resource assignments, effort/cost estimates, and sprint timelines"
        )

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute method for AgentOrchestrator integration
        """
        self.log("Generating project execution plan...")
        plan = self.generate_plan(context, source="Task Routing Analysis")
        return {
            "execution_plan": plan,
            "status": "success"
        }

    def generate_plan(self, input_context: Dict[str, Any], source: str = "Task Routing Analysis") -> Dict[str, Any]:
        """
        Generate execution plan from context or document summary
        """
        doc_text = input_context.get('document_text') or input_context.get('raw_document_text') or ""
        summary = input_context.get('SummaryAgent', {}).get('executive_summary') or doc_text
        tasks = self.get_tasks(input_context)
        
        # If no tasks are present in context, but document_text is available, run DocumentAnalysisAgent on demand
        if not tasks and doc_text:
            try:
                from agents.document_analysis_agent import DocumentAnalysisAgent
                doc_agent = DocumentAnalysisAgent()
                doc_res = doc_agent.execute(input_context)
                tasks = doc_res.get('extracted_tasks', [])
            except Exception as de:
                self.log(f"Dynamic document analysis for plan generation failed: {de}")

        decisions = input_context.get('DecisionAgent', {}).get('final_decisions', [])

        # Fetch active DB resources and AI agents for realistic assignment
        resources_list = self._get_db_resources()
        agents_list = self._get_db_ai_agents()

        system_prompt = f"""You are 'Agile Project Director & Architect AI'.
Given project tasks and resource allocations below, construct a comprehensive JSON Project Execution Plan.

Available Human Resources:
{json.dumps(resources_list, indent=2)}

Available AI Agents:
{json.dumps(agents_list, indent=2)}

Rules for output JSON format (Return ONLY valid JSON matching this exact structure without markdown or explanation):
{{
  "plan_name": "Project Execution Plan - <Project Title>",
  "description": "<Executive summary of project scope and execution strategy>",
  "source": "{source}",
  "total_user_stories": 0,
  "total_story_points": 0,
  "total_effort_hours": 0.0,
  "total_cost": 0.0,
  "sprint_count": 3,
  "start_date": "{datetime.now().strftime('%Y-%m-%d')}",
  "target_end_date": "{(datetime.now() + timedelta(days=42)).strftime('%Y-%m-%d')}",
  "user_stories": [
    {{
      "story_id": "US-101",
      "title": "<User Story Title>",
      "description": "As a <role>, I want <feature> so that <benefit>",
      "acceptance_criteria": ["Given...", "When...", "Then..."],
      "priority": "High|Medium|Low",
      "complexity": "High|Medium|Low",
      "assigned_to": "<Resource or Agent Name>",
      "assigned_type": "Human|AI Agent",
      "story_points": 5,
      "estimated_effort_hours": 40.0,
      "estimated_cost": 3000.0,
      "sprint": "Sprint 1",
      "status": "Ready for Sprint"
    }}
  ],
  "timeline": [
    {{
      "sprint_number": 1,
      "sprint_name": "Sprint 1: Architecture & Foundation",
      "duration_weeks": 2,
      "start_date": "{datetime.now().strftime('%Y-%m-%d')}",
      "end_date": "{(datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')}",
      "key_deliverables": ["Core Setup", "Database Schema"],
      "story_ids": ["US-101"]
    }}
  ],
  "team_allocation": [
    {{
      "name": "<Resource Name>",
      "type": "Human|AI Agent",
      "role": "<Role>",
      "assigned_stories_count": 2,
      "total_hours": 40.0,
      "total_cost": 3000.0
    }}
  ]
}}"""

        user_content = f"Project Context:\n{summary[:2000]}\n\nTask Details ({len(tasks)} tasks):\n{json.dumps(tasks, indent=2)[:3000]}\n\nRouting Decisions:\n{json.dumps(decisions, indent=2)[:3000]}"

        try:
            raw_response = self.call_llm(system_prompt, user_content, temperature=0.3, response_format='json')
            
            # Clean markdown wrappers if present
            clean_json = raw_response.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.startswith("```"):
                clean_json = clean_json[3:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
            clean_json = clean_json.strip()

            plan_dict = json.loads(clean_json)
            plan_dict['source'] = source

            if not plan_dict.get('user_stories') or 'Undefined Project' in plan_dict.get('plan_name', '') or plan_dict.get('total_user_stories', 0) == 0:
                return self._build_heuristic_fallback_plan(tasks, decisions, resources_list, agents_list, source)

            return self._recalculate_totals(plan_dict)
        except Exception as e:
            print("[ProjectExecutionAgent] LLM generation failed/fallback triggered:", e)
            return self._build_heuristic_fallback_plan(tasks, decisions, resources_list, agents_list, source)

    def _get_db_resources(self) -> List[Dict[str, Any]]:
        try:
            return database.execute_query("SELECT resource_id, name, role, skills, cost_per_hour FROM human_resources LIMIT 10")
        except Exception:
            return [{"name": "Senior Full Stack Dev", "role": "Developer", "cost_per_hour": 75.0}]

    def _get_db_ai_agents(self) -> List[Dict[str, Any]]:
        try:
            return database.execute_query("SELECT agent_id, agent_name, capabilities, cost_per_hour FROM ai_agents LIMIT 10")
        except Exception:
            return [{"agent_name": "Code Generation Agent", "capabilities": "Python, API", "cost_per_hour": 15.0}]

    def _recalculate_totals(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        stories = plan.get('user_stories', [])
        total_pts = sum(s.get('story_points', 0) for s in stories)
        total_hours = sum(s.get('estimated_effort_hours', 0) for s in stories)
        total_cost = sum(s.get('estimated_cost', 0) for s in stories)

        plan['total_user_stories'] = len(stories)
        plan['total_story_points'] = total_pts
        plan['total_effort_hours'] = round(total_hours, 1)
        plan['total_cost'] = round(total_cost, 2)
        return plan

    def _build_heuristic_fallback_plan(self, tasks: List[Any], decisions: List[Any], resources: List[Any], agents: List[Any], source: str) -> Dict[str, Any]:
        """Build structured fallback plan if LLM call fails"""
        user_stories = []
        sprint_1_ids = []
        sprint_2_ids = []
        sprint_3_ids = []

        start_dt = datetime.now()
        
        sample_tasks = tasks if tasks else [
            {"task_name": "Core System Architecture Setup", "complexity": "High", "estimated_effort": 32},
            {"task_name": "API & Backend Microservices Integration", "complexity": "Medium", "estimated_effort": 24},
            {"task_name": "Glassmorphism UI & Dashboard Components", "complexity": "Medium", "estimated_effort": 20},
            {"task_name": "AI Agent & RAG Service Pipeline Integration", "complexity": "High", "estimated_effort": 40},
            {"task_name": "SLA & Cost Monitoring Guardrails Implementation", "complexity": "Low", "estimated_effort": 16}
        ]

        default_res = resources[0]['name'] if resources else "Senior Architect"
        default_cost = resources[0]['cost_per_hour'] if resources else 75.0

        for idx, t in enumerate(sample_tasks, 1):
            sid = f"US-{100 + idx}"
            tname = t.get('task_name') or f"Project Execution Task {idx}"
            effort = float(t.get('estimated_effort') or 24)
            pts = 8 if effort >= 32 else (5 if effort >= 20 else 3)
            sprint_name = f"Sprint {(idx % 3) + 1}"
            
            res_assigned = default_res
            res_type = "Human"
            if idx % 2 == 0 and agents:
                res_assigned = agents[0].get('agent_name', 'AI Code Generator')
                res_type = "AI Agent"
                cost_hr = float(agents[0].get('cost_per_hour', 15.0))
            else:
                cost_hr = default_cost

            cost_est = round(effort * cost_hr, 2)

            story = {
                "story_id": sid,
                "title": f"Implement {tname}",
                "description": f"As a product owner, I want {tname} implemented with zero defects and full SLA compliance.",
                "acceptance_criteria": [
                    f"Requirement logic for {tname} is fully verified",
                    "Unit tests and compliance checks pass 100%",
                    "Documentation and API endpoints are registered"
                ],
                "priority": "High" if idx <= 2 else "Medium",
                "complexity": t.get('complexity', 'Medium'),
                "assigned_to": res_assigned,
                "assigned_type": res_type,
                "story_points": pts,
                "estimated_effort_hours": effort,
                "estimated_cost": cost_est,
                "sprint": sprint_name,
                "status": "Ready for Sprint"
            }
            user_stories.append(story)

            if sprint_name == "Sprint 1":
                sprint_1_ids.append(sid)
            elif sprint_name == "Sprint 2":
                sprint_2_ids.append(sid)
            else:
                sprint_3_ids.append(sid)

        timeline = [
            {
                "sprint_number": 1,
                "sprint_name": "Sprint 1: Core Architecture & Setup",
                "duration_weeks": 2,
                "start_date": start_dt.strftime('%Y-%m-%d'),
                "end_date": (start_dt + timedelta(days=14)).strftime('%Y-%m-%d'),
                "key_deliverables": ["Environment Setup", "Core Data Models"],
                "story_ids": sprint_1_ids
            },
            {
                "sprint_number": 2,
                "sprint_name": "Sprint 2: Service Logic & Integrations",
                "duration_weeks": 2,
                "start_date": (start_dt + timedelta(days=14)).strftime('%Y-%m-%d'),
                "end_date": (start_dt + timedelta(days=28)).strftime('%Y-%m-%d'),
                "key_deliverables": ["API Endpoints", "UI Dashboard"],
                "story_ids": sprint_2_ids
            },
            {
                "sprint_number": 3,
                "sprint_name": "Sprint 3: AI Agents & Final Deployment",
                "duration_weeks": 2,
                "start_date": (start_dt + timedelta(days=28)).strftime('%Y-%m-%d'),
                "end_date": (start_dt + timedelta(days=42)).strftime('%Y-%m-%d'),
                "key_deliverables": ["AI Agent Orchestration", "End-to-End Release"],
                "story_ids": sprint_3_ids
            }
        ]

        total_pts = sum(s['story_points'] for s in user_stories)
        total_effort = sum(s['estimated_effort_hours'] for s in user_stories)
        total_cost = sum(s['estimated_cost'] for s in user_stories)

        return {
            "plan_name": f"Project Execution Plan - {source}",
            "description": "Comprehensive Agile project plan detailing User Stories, Resource/Agent allocations, Fibonacci effort points, and 3-Sprint milestone roadmap.",
            "source": source,
            "total_user_stories": len(user_stories),
            "total_story_points": total_pts,
            "total_effort_hours": round(total_effort, 1),
            "total_cost": round(total_cost, 2),
            "sprint_count": 3,
            "start_date": start_dt.strftime('%Y-%m-%d'),
            "target_end_date": (start_dt + timedelta(days=42)).strftime('%Y-%m-%d'),
            "user_stories": user_stories,
            "timeline": timeline,
            "team_allocation": [
                {
                    "name": default_res,
                    "type": "Human",
                    "role": "Lead Architect",
                    "assigned_stories_count": len([s for s in user_stories if s['assigned_type'] == 'Human']),
                    "total_hours": sum(s['estimated_effort_hours'] for s in user_stories if s['assigned_type'] == 'Human'),
                    "total_cost": sum(s['estimated_cost'] for s in user_stories if s['assigned_type'] == 'Human')
                }
            ]
        }
