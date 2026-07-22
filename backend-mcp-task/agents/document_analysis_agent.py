"""
Document Analysis Agent - Agent 1
Extracts requirements, tasks, skills, and priorities from uploaded documents
"""
from agents import Agent
from typing import Dict, Any
import json
import pdfminer
from pdfminer.high_level import extract_text
from docx import Document as DocxDocument

class DocumentAnalysisAgent(Agent):
    """
    Analyzes uploaded project documents and extracts structured task information.
    This is the first agent in the pipeline (LLM Call 1).
    """
    
    def __init__(self):
        super().__init__(
            name="DocumentAnalysisAgent",
            description="Extracts requirements, tasks, skills, and priorities from documents"
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract task information from the uploaded document
        
        Args:
            context: Contains 'document_path' and 'document_content'
        
        Returns:
            Extracted tasks with requirements
        """
        self.log("Starting document analysis...")
        
        # Get document content from context
        document_text = context.get('document_text', '')
        document_path = context.get('document_path', '')
        
        if not document_text:
            # If no text provided, try to extract from file path
            if document_path:
                document_text = self.extract_text_from_file(document_path)
            else:
                return {"error": "No document text or path provided"}
        
        # Use LLM to extract structured task information
        system_prompt = """You are a project analyst expert at extracting task information from project documents.
Extract all tasks mentioned in the document and structure them with the following information:
- Task name
- Task description
- Required skills (comma-separated)
- Estimated complexity (Low/Medium/High)
- Priority (Critical/High/Medium/Low)
- Estimated effort in hours (best guess if not specified)

Return your response as a JSON object with a "tasks" array. Each task should be an object with fields:
task_name, description, skills_required, complexity, priority, estimated_effort

If the document doesn't clearly specify something, make reasonable inferences based on the description."""
        
        user_message = f"""Analyze this project document and extract all tasks:

{document_text[:5000]}  

Extract all tasks with their requirements, skills needed, complexity, and priorities."""
        
        # Call LLM
        llm_response = self.call_llm(system_prompt, user_message, temperature=0.3, response_format='json')
        
        try:
            extracted_data = json.loads(llm_response)
            tasks = extracted_data.get('tasks', [])
            
            self.log(f"Extracted {len(tasks)} tasks from document")
            
            return {
                "extracted_tasks": tasks,
                "task_count": len(tasks),
                "document_summary": document_text[:500] if document_text else "",
                "status": "success"
            }
        
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse LLM response as JSON: {str(e)}")
            # Fallback: return raw response
            return {
                "extracted_tasks": [],
                "raw_response": llm_response,
                "status": "partial_success",
                "error": "Could not parse JSON response"
            }
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file formats"""
        try:
            if file_path.lower().endswith('.pdf'):
                return extract_text(file_path)
            elif file_path.lower().endswith('.docx'):
                doc = DocxDocument(file_path)
                return '\n'.join([para.text for para in doc.paragraphs])
            elif file_path.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return ""
        except Exception as e:
            self.log(f"Error extracting text from file: {str(e)}")
            return ""
