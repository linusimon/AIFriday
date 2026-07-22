"""
Data Enrichment Agent - Agent 3
Enriches tasks with contextual information using RAG knowledge base
"""
from agents import Agent
from typing import Dict, Any, List
import json

_rag_service = None

class DataEnrichmentAgent(Agent):
    """
    Enriches task data with additional context from RAG knowledge base.
    This is the third agent in the pipeline (LLM Call 3).
    """
    
    def __init__(self):
        super().__init__(
            name="DataEnrichmentAgent",
            description="Adds context and metadata to tasks using RAG"
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich tasks with additional context
        
        Args:
            context: Contains 'DataCleansingAgent' results
        
        Returns:
            Enriched tasks with additional metadata
        """
        self.log("Starting data enrichment...")
        
        # Get cleansed tasks from previous agent
        cleansing = context.get('DataCleansingAgent', {})
        cleansed_tasks = cleansing.get('cleansed_tasks', [])
        
        if not cleansed_tasks:
            self.log("No tasks to enrich")
            return {
                "enriched_tasks": [],
                "status": "no_data"
            }
        
        # Enrich each task with contextual information
        enriched_tasks = []
        
        for task in cleansed_tasks:
            enriched_task = self.enrich_task(task)
            enriched_tasks.append(enriched_task)
        
        self.log(f"Enriched {len(enriched_tasks)} tasks")
        
        return {
            "enriched_tasks": enriched_tasks,
            "enrichment_count": len(enriched_tasks),
            "status": "success"
        }
    
    def enrich_task(self, task: Dict) -> Dict:
        """Enrich a single task with additional context"""
        
        # Search RAG knowledge base for relevant context
        global _rag_service
        if _rag_service is None:
            try:
                from rag_service import RAGService
                _rag_service = RAGService()
            except Exception as e:
                self.log(f"Failed to initialize RAGService: {str(e)}")
                
        rag_context = ""
        if _rag_service:
            try:
                query = f"{task.get('task_name')} {task.get('description')} {task.get('skills_required')}"
                rag_results = _rag_service.search_knowledge(query, top_k=3)
                if rag_results:
                    rag_context = "\nContext retrieved from Corporate Knowledge Base:\n" + \
                                  "\n".join([f"- [{res['category']}] {res['content']}" for res in rag_results])
            except Exception as e:
                self.log(f"RAG search failed during enrichment: {str(e)}")
            
        # Use LLM to add context and expand understanding
        system_prompt = """You are a technical project expert. Enrich the given task with additional context and metadata.
        
Add the following enrichments:
1. Expand abbreviated terms in the description
2. Add technical context about the skills required
3. Suggest potential challenges or considerations
4. Identify any dependencies or prerequisites
5. Add domain-specific insights

Return a JSON object with the original task fields plus:
- expanded_description: More detailed description
- technical_context: Technical insights about the task
- potential_challenges: List of potential challenges
- prerequisites: Any required prerequisites
- domain_category: Category (e.g., "Backend", "Frontend", "Data Science", "DevOps")"""
        
        task_json = json.dumps(task, indent=2)
        user_message = f"""Enrich this task with additional context:

{task_json}
{rag_context}

Add meaningful context that would help in resource assignment."""
        
        # Call LLM
        llm_response = self.call_llm(system_prompt, user_message, temperature=0.5, response_format='json')
        
        try:
            enriched = json.loads(llm_response)
            
            # Merge enriched data with original task
            enriched_task = task.copy()
            enriched_task.update({
                "expanded_description": enriched.get('expanded_description', task.get('description', '')),
                "technical_context": enriched.get('technical_context', ''),
                "potential_challenges": enriched.get('potential_challenges', []),
                "prerequisites": enriched.get('prerequisites', []),
                "domain_category": enriched.get('domain_category', 'General')
            })
            
            return enriched_task
        
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse enrichment for task {task.get('task_name')}: {str(e)}")
            # Return original task with basic enrichment
            return self.basic_enrichment(task)
    
    def basic_enrichment(self, task: Dict) -> Dict:
        """Basic enrichment without LLM"""
        enriched = task.copy()
        
        skills_raw = task.get('skills_required', '')
        if isinstance(skills_raw, list):
            skills = " ".join([str(s) for s in skills_raw]).lower()
        else:
            skills = str(skills_raw).lower()
        
        if any(word in skills for word in ['python', 'java', 'backend', 'api', 'database']):
            domain = 'Backend Development'
        elif any(word in skills for word in ['react', 'angular', 'frontend', 'ui', 'css']):
            domain = 'Frontend Development'
        elif any(word in skills for word in ['machine learning', 'data science', 'ml', 'ai']):
            domain = 'Data Science'
        elif any(word in skills for word in ['devops', 'docker', 'kubernetes', 'ci/cd']):
            domain = 'DevOps'
        elif any(word in skills for word in ['mobile', 'ios', 'android']):
            domain = 'Mobile Development'
        else:
            domain = 'General'
        
        enriched.update({
            "expanded_description": task.get('description', ''),
            "technical_context": f"Requires skills in {task.get('skills_required', 'various technologies')}",
            "potential_challenges": [],
            "prerequisites": [],
            "domain_category": domain
        })
        
        return enriched
