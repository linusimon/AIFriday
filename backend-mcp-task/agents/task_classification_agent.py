"""
Task Classification Agent - Agent 4
Determines task category, complexity, and effort estimation
"""
from agents import Agent
from typing import Dict, Any, List
import json

class TaskClassificationAgent(Agent):
    """
    Classifies tasks by category, complexity, and refines effort estimates.
    This is the fourth agent in the pipeline (LLM Call 4).
    """
    
    def __init__(self):
        super().__init__(
            name="TaskClassificationAgent",
            description="Classifies tasks and estimates complexity and effort"
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify and refine task estimates
        
        Args:
            context: Contains 'DataEnrichmentAgent' results
        
        Returns:
            Classified tasks with refined estimates
        """
        self.log("Starting task classification...")
        
        # Get enriched tasks from previous agent
        enrichment = context.get('DataEnrichmentAgent', {})
        enriched_tasks = enrichment.get('enriched_tasks', [])
        
        if not enriched_tasks:
            self.log("No tasks to classify")
            return {
                "classified_tasks": [],
                "status": "no_data"
            }
        
        # Classify all tasks in batch
        classified_tasks = self.classify_tasks_batch(enriched_tasks)
        
        # Generate classification summary
        summary = self.generate_classification_summary(classified_tasks)
        
        self.log(f"Classified {len(classified_tasks)} tasks")
        
        return {
            "classified_tasks": classified_tasks,
            "classification_summary": summary,
            "status": "success"
        }
    
    def classify_tasks_batch(self, tasks: List[Dict]) -> List[Dict]:
        """Classify all tasks in a single LLM call for efficiency"""
        
        system_prompt = """You are an expert project estimator and task classifier.

For each task, provide:
1. Refined complexity assessment (Low/Medium/High) based on:
   - Technical complexity
   - Number of skills required
   - Potential challenges
   - Dependencies

2. Refined effort estimate (hours) based on:
   - Complexity
   - Scope of work
   - Industry standards

3. Task category (one of):
   - Development (Backend/Frontend/Full Stack/Mobile)
   - Data Engineering
   - Machine Learning
   - DevOps
   - UI/UX Design
   - Quality Assurance
   - Security
   - Architecture
   - Documentation

4. Confidence score (0-100) for your assessment

Return a JSON object with a "classified_tasks" array. Each task should have:
task_id (use index), task_name, refined_complexity, refined_effort, category, confidence_score, classification_reasoning"""
        
        # Prepare tasks for classification (limit fields for token efficiency)
        task_summaries = []
        for i, task in enumerate(tasks):
            task_summaries.append({
                "index": i,
                "task_name": task.get('task_name', ''),
                "description": task.get('description', ''),
                "skills_required": task.get('skills_required', ''),
                "current_complexity": task.get('complexity', ''),
                "current_effort": task.get('estimated_effort', 0),
                "domain_category": task.get('domain_category', '')
            })
        
        tasks_json = json.dumps(task_summaries, indent=2)
        user_message = f"""Classify and refine estimates for these tasks:

{tasks_json}

Provide refined complexity, effort estimates, and categorization."""
        
        # Call LLM
        llm_response = self.call_llm(system_prompt, user_message, temperature=0.3, response_format='json')
        
        try:
            classification_data = json.loads(llm_response)
            classified_list = classification_data.get('classified_tasks', [])
            
            # Merge classifications back into original tasks
            classified_tasks = []
            for i, task in enumerate(tasks):
                classified_task = task.copy()
                
                # Find corresponding classification
                classification = next((c for c in classified_list if c.get('task_id') == i or c.get('index') == i), None)
                
                if classification:
                    classified_task.update({
                        "complexity": classification.get('refined_complexity', task.get('complexity', 'Medium')),
                        "estimated_effort": classification.get('refined_effort', task.get('estimated_effort', 8)),
                        "category": classification.get('category', task.get('domain_category', 'General')),
                        "classification_confidence": classification.get('confidence_score', 70),
                        "classification_reasoning": classification.get('classification_reasoning', '')
                    })
                
                classified_tasks.append(classified_task)
            
            return classified_tasks
        
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse classification response: {str(e)}")
            # Return tasks with basic classification
            return [self.basic_classification(task) for task in tasks]
    
    def basic_classification(self, task: Dict) -> Dict:
        """Basic classification without LLM"""
        classified = task.copy()
        
        # Keep existing complexity if present
        complexity = task.get('complexity', 'Medium')
        effort = task.get('estimated_effort', 8)
        
        # Adjust effort based on complexity if needed
        if complexity == 'High' and effort < 20:
            effort = 40
        elif complexity == 'Low' and effort > 20:
            effort = 8
        
        classified.update({
            "complexity": complexity,
            "estimated_effort": effort,
            "category": task.get('domain_category', 'General'),
            "classification_confidence": 60,
            "classification_reasoning": "Basic classification applied"
        })
        
        return classified
    
    def generate_classification_summary(self, tasks: List[Dict]) -> Dict:
        """Generate summary statistics of classifications"""
        total = len(tasks)
        
        complexity_dist = {"Low": 0, "Medium": 0, "High": 0}
        category_dist = {}
        total_effort = 0
        
        for task in tasks:
            complexity = task.get('complexity', 'Medium')
            complexity_dist[complexity] = complexity_dist.get(complexity, 0) + 1
            
            category = task.get('category', 'General')
            category_dist[category] = category_dist.get(category, 0) + 1
            
            total_effort += task.get('estimated_effort', 0)
        
        return {
            "total_tasks": total,
            "complexity_distribution": complexity_dist,
            "category_distribution": category_dist,
            "total_estimated_effort": round(total_effort, 2),
            "average_effort_per_task": round(total_effort / total if total > 0 else 0, 2)
        }
