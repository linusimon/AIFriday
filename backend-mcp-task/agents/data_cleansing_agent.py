"""
Data Cleansing Agent - Agent 2
Normalizes extracted data, removes duplicates, and standardizes formats
"""
from agents import Agent
from typing import Dict, Any, List
import json

class DataCleansingAgent(Agent):
    """
    Cleanses and normalizes the extracted task data.
    This is the second agent in the pipeline (LLM Call 2).
    """
    
    def __init__(self):
        super().__init__(
            name="DataCleansingAgent",
            description="Normalizes extracted data and removes inconsistencies"
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cleanse and normalize the extracted tasks
        
        Args:
            context: Contains 'DocumentAnalysisAgent' results
        
        Returns:
            Cleansed and normalized tasks
        """
        self.log("Starting data cleansing...")
        
        # Get extracted tasks from previous agent
        doc_analysis = context.get('DocumentAnalysisAgent', {})
        extracted_tasks = doc_analysis.get('extracted_tasks', [])
        
        if not extracted_tasks:
            self.log("No tasks to cleanse")
            return {
                "cleansed_tasks": [],
                "status": "no_data"
            }
        
        # Use LLM to cleanse and normalize the data
        system_prompt = """You are a data quality expert. Your job is to cleanse and normalize task data.

Perform the following:
1. Remove duplicate tasks (same or very similar task names)
2. Standardize skill names (e.g., "Python programming" -> "Python", "ReactJS" -> "React")
3. Ensure complexity is one of: Low, Medium, High
4. Ensure priority is one of: Critical, High, Medium, Low
5. Validate and normalize estimated effort (must be a positive number)
6. Expand abbreviations in descriptions
7. Ensure each task has all required fields

Return a JSON object with a "cleansed_tasks" array containing the cleaned tasks."""
        
        tasks_json = json.dumps(extracted_tasks, indent=2)
        user_message = f"""Cleanse and normalize these extracted tasks:

{tasks_json}

Return the cleansed data in the same structure."""
        
        # Call LLM
        llm_response = self.call_llm(system_prompt, user_message, temperature=0.2, response_format='json')
        
        try:
            cleansed_data = json.loads(llm_response)
            cleansed_tasks = cleansed_data.get('cleansed_tasks', [])
            
            self.log(f"Cleansed {len(cleansed_tasks)} tasks (from {len(extracted_tasks)} original)")
            
            # Basic validation
            validated_tasks = self.validate_tasks(cleansed_tasks)
            
            return {
                "cleansed_tasks": validated_tasks,
                "original_count": len(extracted_tasks),
                "cleansed_count": len(validated_tasks),
                "duplicates_removed": len(extracted_tasks) - len(validated_tasks),
                "status": "success"
            }
        
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse LLM response: {str(e)}")
            # Fallback: return original tasks with basic normalization
            return {
                "cleansed_tasks": self.basic_cleansing(extracted_tasks),
                "status": "fallback",
                "error": "LLM parsing failed, used basic cleansing"
            }
    
    def validate_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """Apply basic validation rules"""
        validated = []
        
        for i, task in enumerate(tasks):
            # Ensure required fields exist
            if 'task_name' not in task or not task['task_name']:
                continue
            
            # Assign persistent task_id
            task['task_id'] = i + 1
            
            # Normalize complexity
            complexity = task.get('complexity', 'Medium')
            if complexity not in ['Low', 'Medium', 'High']:
                task['complexity'] = 'Medium'
            else:
                task['complexity'] = complexity
            
            # Normalize priority
            priority = task.get('priority', 'Medium')
            if priority not in ['Critical', 'High', 'Medium', 'Low']:
                task['priority'] = 'Medium'
            else:
                task['priority'] = priority
            
            # Ensure estimated_effort is a number
            try:
                task['estimated_effort'] = float(task.get('estimated_effort', 8))
            except (ValueError, TypeError):
                task['estimated_effort'] = 8
            
            # Ensure skills_required exists
            if 'skills_required' not in task:
                task['skills_required'] = ''
            
            validated.append(task)
        
        return validated
    
    def basic_cleansing(self, tasks: List[Dict]) -> List[Dict]:
        """Basic cleansing without LLM"""
        # Remove exact duplicates and apply basic normalization
        seen = set()
        cleansed = []
        
        for task in tasks:
            task_key = task.get('task_name', '').lower().strip()
            if task_key and task_key not in seen:
                seen.add(task_key)
                cleansed.append(self.validate_tasks([task])[0])
        
        return cleansed
