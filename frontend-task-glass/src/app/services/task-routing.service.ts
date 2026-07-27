import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  AnalysisResult,
  HumanResource,
  AIAgent,
  Project,
  Task,
  KnowledgeDocument,
  ExpertAnalysis,
  SLARule,
  CostModel,
  MCPServer
} from '../models/task-routing.model';

@Injectable({
  providedIn: 'root'
})
export class TaskRoutingService {
  private apiUrl = '/api';

  constructor(private http: HttpClient) {}

  // ========== Task Analysis ==========
  
  analyzeDocument(file: File): Observable<AnalysisResult> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<AnalysisResult>(`${this.apiUrl}/task-routing/analyze`, formData);
  }

  analyzeDocumentText(text: string): Observable<AnalysisResult> {
    return this.http.post<AnalysisResult>(`${this.apiUrl}/task-routing/analyze`, {
      document_text: text
    });
  }

  getAnalysisHistory(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/task-routing/history`);
  }

  // ========== MCP Servers ==========

  getMCPStatus(): Observable<{ success: boolean; servers: MCPServer[]; total_servers: number }> {
    return this.http.get<{ success: boolean; servers: MCPServer[]; total_servers: number }>(
      `${this.apiUrl}/mcp/status`
    );
  }

  callMCPTool(server: string, tool: string, params: any = {}): Observable<any> {
    return this.http.post(`${this.apiUrl}/mcp/${server}/${tool}`, params);
  }

  // ========== Admin: Resources ==========

  getHumanResources(): Observable<HumanResource[]> {
    return this.http.get<HumanResource[]>(`${this.apiUrl}/admin/human-resources`);
  }

  createHumanResource(resource: Partial<HumanResource>): Observable<any> {
    return this.http.post(`${this.apiUrl}/admin/human-resources`, resource);
  }

  updateHumanResource(id: number, resource: Partial<HumanResource>): Observable<any> {
    return this.http.put(`${this.apiUrl}/admin/human-resources/${id}`, resource);
  }

  deleteHumanResource(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/admin/human-resources/${id}`);
  }

  getAIAgents(): Observable<AIAgent[]> {
    return this.http.get<AIAgent[]>(`${this.apiUrl}/admin/ai-agents`);
  }

  createAIAgent(agent: Partial<AIAgent>): Observable<any> {
    return this.http.post(`${this.apiUrl}/admin/ai-agents`, agent);
  }

  updateAIAgent(id: number, agent: Partial<AIAgent>): Observable<any> {
    return this.http.put(`${this.apiUrl}/admin/ai-agents/${id}`, agent);
  }

  deleteAIAgent(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/admin/ai-agents/${id}`);
  }

  // ========== Admin: Projects ==========

  getProjects(): Observable<Project[]> {
    return this.http.get<Project[]>(`${this.apiUrl}/admin/projects`);
  }

  createProject(project: Partial<Project>): Observable<any> {
    return this.http.post(`${this.apiUrl}/admin/projects`, project);
  }

  updateProject(id: number, project: Partial<Project>): Observable<any> {
    return this.http.put(`${this.apiUrl}/admin/projects/${id}`, project);
  }

  deleteProject(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/admin/projects/${id}`);
  }

  // ========== Admin: Tasks ==========

  getTasks(): Observable<Task[]> {
    return this.http.get<Task[]>(`${this.apiUrl}/admin/tasks`);
  }

  createTask(task: Partial<Task>): Observable<any> {
    return this.http.post(`${this.apiUrl}/admin/tasks`, task);
  }

  updateTask(id: number, task: Partial<Task>): Observable<any> {
    return this.http.put(`${this.apiUrl}/admin/tasks/${id}`, task);
  }

  deleteTask(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/admin/tasks/${id}`);
  }

  // ========== Admin: Knowledge Base ==========

  uploadKnowledge(file: File, category: string): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);
    return this.http.post(`${this.apiUrl}/knowledge/upload`, formData);
  }

  searchKnowledge(query: string, topK: number = 5): Observable<any> {
    return this.http.post(`${this.apiUrl}/knowledge/search`, {
      query: query,
      top_k: topK
    });
  }

  // ========== Admin: Expert Analysis ==========

  getExpertAnalysis(): Observable<ExpertAnalysis[]> {
    return this.http.get<ExpertAnalysis[]>(`${this.apiUrl}/admin/expert-analysis`);
  }

  createExpertAnalysis(analysis: Partial<ExpertAnalysis>): Observable<any> {
    return this.http.post(`${this.apiUrl}/admin/expert-analysis`, analysis);
  }

  updateExpertAnalysis(id: number, analysis: Partial<ExpertAnalysis>): Observable<any> {
    return this.http.put(`${this.apiUrl}/admin/expert-analysis/${id}`, analysis);
  }

  deleteExpertAnalysis(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/admin/expert-analysis/${id}`);
  }

  // ========== Admin: SLA Rules ==========

  getSLARules(): Observable<SLARule[]> {
    return this.http.get<SLARule[]>(`${this.apiUrl}/admin/sla-rules`);
  }

  createSLARule(rule: Partial<SLARule>): Observable<any> {
    return this.http.post(`${this.apiUrl}/admin/sla-rules`, rule);
  }

  updateSLARule(id: number, rule: Partial<SLARule>): Observable<any> {
    return this.http.put(`${this.apiUrl}/admin/sla-rules/${id}`, rule);
  }

  deleteSLARule(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/admin/sla-rules/${id}`);
  }

  // ========== Admin: Cost Models ==========

  getCostModels(): Observable<CostModel[]> {
    return this.http.get<CostModel[]>(`${this.apiUrl}/admin/cost-models`);
  }

  createCostModel(model: Partial<CostModel>): Observable<any> {
    return this.http.post(`${this.apiUrl}/admin/cost-models`, model);
  }

  updateCostModel(id: number, model: Partial<CostModel>): Observable<any> {
    return this.http.put(`${this.apiUrl}/admin/cost-models/${id}`, model);
  }

  deleteCostModel(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/admin/cost-models/${id}`);
  }
}
