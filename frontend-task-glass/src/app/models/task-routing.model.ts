// Task Routing System Models

export interface HumanResource {
  resource_id: number;
  name: string;
  role: string;
  skills: string;
  experience: number;
  availability: 'Available' | 'Busy' | 'On Leave';
  current_workload: number;
  quality_score: number;
  performance_score: number;
  cost_per_hour: number;
}

export interface AIAgent {
  agent_id: number;
  name: string;
  agent_type: string;
  capabilities: string;
  specialization: string;
  availability: 'Available' | 'Busy' | 'Maintenance';
  performance_metrics: string;
  cost_per_hour: number;
}

export interface Project {
  project_id: number;
  name: string;
  description: string;
  start_date: string;
  end_date: string;
  status: 'Planning' | 'Active' | 'On Hold' | 'Completed';
  priority: 'Low' | 'Medium' | 'High' | 'Critical';
  budget: number;
}

export interface Task {
  task_id: number;
  project_id: number;
  name: string;
  description: string;
  skills_required: string;
  complexity: 'Low' | 'Medium' | 'High';
  priority: 'Low' | 'Medium' | 'High' | 'Critical';
  estimated_effort: number;
  status: 'Pending' | 'In Progress' | 'Completed' | 'On Hold';
  created_date: string;
}

export interface ResourceMatch {
  resource_id: number;
  resource_name: string;
  resource_type: 'human' | 'ai';
  match_score: number;
  skill_match: string[];
  missing_skills: string[];
  availability: string;
  current_workload: number;
  cost_per_hour: number;
  estimated_cost: number;
  quality_score: number;
  sla_compliance: number;
  risk_level: 'Low' | 'Medium' | 'High';
}

export interface TaskAssignment {
  task_name: string;
  task_description: string;
  complexity: string;
  estimated_effort: number;
  skills_required: string[];
  recommended_resource: {
    resource_id: number;
    name: string;
    type: 'human' | 'ai';
    confidence_score: number;
    reasoning: string;
  };
  resource_options: ResourceMatch[];
  cost_analysis: {
    recommended_cost: number;
    cheapest_cost: number;
    premium_cost: number;
    potential_savings: number;
  };
  risk_assessment: {
    risk_level: string;
    risk_factors: string[];
    mitigation_strategies: string[];
  };
  sla_compliance: {
    expected_completion: string;
    sla_breach_risk: number;
  };
}

export interface AnalysisResult {
  analysis_id?: string;
  task_count: number;
  success: boolean;
  message: string;
  report: {
    analysis_overview: {
      total_tasks: number;
      human_assignments: number;
      ai_assignments: number;
      total_estimated_effort: number;
      total_estimated_cost: number;
      high_risk_tasks: number;
    };
    task_assignments: TaskAssignment[];
    executive_summary: string;
    detailed_recommendations: string[];
    next_steps: string[];
    cost_analysis: {
      total_cost: number;
      cost_summary: any;
      optimization_potential: number;
    };
    risk_assessment: {
      overall_risk: string;
      high_risk_count: number;
      risk_distribution: any;
    };
    workload_insights: {
      overloaded_resources: number;
      underutilized_resources: number;
      recommendations: string[];
    };
  };
}

export interface KnowledgeDocument {
  document_id?: number;
  filename: string;
  category: string;
  upload_date?: string;
  file_size?: number;
  status?: string;
}

export interface ExpertAnalysis {
  analysis_id?: number;
  category: string;
  title: string;
  content: string;
  author?: string;
  created_date?: string;
}

export interface SLARule {
  rule_id?: number;
  priority: string;
  max_response_time: number;
  max_resolution_time: number;
  quality_threshold: number;
}

export interface CostModel {
  cost_id?: number;
  resource_type: string;
  role: string;
  cost_per_hour: number;
  quality_multiplier: number;
  complexity_multiplier?: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  image?: string;
}

export interface ChatSession {
  session_id: string;
  messages: ChatMessage[];
  context?: any;
}

export interface MCPServer {
  name: string;
  description: string;
  tools?: string[];
}

export interface MCPToolCall {
  server: string;
  tool: string;
  params: any;
}

export interface VoiceRequest {
  audio_data: string;
  format: string;
}

export interface OCRRequest {
  image_data: string;
  format: string;
}
