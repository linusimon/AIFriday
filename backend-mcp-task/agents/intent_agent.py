"""
Task Intent Classification Agent for analyzing input intent in Task Routing & Project Intelligence.
"""
import re
from typing import Dict, Any

INTENT_CATEGORIES = [
    'FULL_TASK_ROUTING_ANALYSIS',
    'EXECUTION_PLAN_GENERATION',
    'RESOURCE_MATCHING_INQUIRY',
    'COST_SLA_OPTIMIZATION',
    'POLICY_FAQ_INQUIRY',
    'GENERAL_ASSISTANT_CONVERSATION'
]

class TaskIntentAgent:
    """
    Analyzes input query text or document text to classify user intent
    and dynamically determine which specialist agents should be dispatched.
    """
    
    def classify(self, text: str) -> Dict[str, Any]:
        t = (text or "").lower().strip()

        if not t:
            return {
                'intent': 'GENERAL_ASSISTANT_CONVERSATION',
                'confidence': 0.70,
                'description': 'Empty input, routing to general assistant'
            }

        # 1. Execution Plan Generation Intent
        if re.search(r'\b(execution plan|user story|user stories|sprint plan|sprint roadmap|story points|backlog|create plan|project plan)\b', t):
            return {
                'intent': 'EXECUTION_PLAN_GENERATION',
                'confidence': 0.96,
                'description': 'Request for Agile User Stories, resource assignments, and sprint timeline roadmap'
            }

        # 2. Resource Matching Inquiry Intent
        if re.search(r'\b(resource|resources|developer|developers|engineer|engineers|architect|availability|available|who can|which agent|skills|workload)\b', t) and re.search(r'\b(find|search|available|match|who|list|get|show|recommend|identify|assign)\b', t):
            return {
                'intent': 'RESOURCE_MATCHING_INQUIRY',
                'confidence': 0.94,
                'description': 'Inquiry regarding human resource or AI agent matching, skills, and availability'
            }

        # 3. Cost & SLA Optimization Intent
        if re.search(r'\b(cost|costs|budget|sla|rate|rates|hourly|cheapest|penalty|escalation|weight)\b', t) and re.search(r'\b(optimize|optimization|reduce|save|risk|model|rule|trade-off|compliance|limit)\b', t):
            return {
                'intent': 'COST_SLA_OPTIMIZATION',
                'confidence': 0.93,
                'description': 'Inquiry regarding cost models, hourly rate trade-offs, and SLA risk mitigation'
            }

        # 4. Policy & Compliance FAQ Intent
        if re.search(r'\b(policy|policies|compliance|faq|terms|guideline|guidelines|privacy|security|gdpr)\b', t):
            return {
                'intent': 'POLICY_FAQ_INQUIRY',
                'confidence': 0.90,
                'description': 'Inquiry regarding corporate policies, compliance guidelines, or SLA standards'
            }

        # 5. Full Task Routing Analysis Intent (Matches task requirements, architecture specs, or multi-task input)
        if re.search(r'\b(task|tasks|build|implement|develop|create|system|api|ui|dashboard|project|requirement|requirements|analyze|module|feature|architecture|database|service)\b', t) or len(t.split()) >= 3:
            return {
                'intent': 'FULL_TASK_ROUTING_ANALYSIS',
                'confidence': 0.95,
                'description': 'Full multi-stage task extraction, cleansing, classification, resource matching, SLA & cost optimization'
            }

        # 6. General Assistant / Conversational Greeting Intent
        return {
            'intent': 'GENERAL_ASSISTANT_CONVERSATION',
            'confidence': 0.80,
            'description': 'General conversational assistant query'
        }

task_intent_agent = TaskIntentAgent()
