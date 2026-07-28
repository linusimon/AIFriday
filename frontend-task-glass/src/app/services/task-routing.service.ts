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

  // ========== Persistent Analysis State Across Tabs ==========
  public selectedFile: File | null = null;
  public documentText: string = '';
  public inputMode: 'file' | 'text' = 'file';
  public activeResultTab: 'overview' | 'matrix' | 'recommendations' = 'overview';
  public analyzing: boolean = false;
  public analysisResult: AnalysisResult | null = null;
  public error: string | null = null;
  public currentStep: number = 0;
  public totalSteps: number = 7;
  public progressPercent: number = 0;
  public currentAgent: string = '';
  public agentLogs: { agent: string; status: string; step: number; message: string; timestamp: string }[] = [];
  public extractedTasksPreview: any[] = [];
  public analysisTimestamp: number = 0;

  constructor(private http: HttpClient) {}

  getAnalysisContextSummary(): string | null {
    if (!this.analysisResult) return null;
    let summary = `DOCUMENT ANALYSIS SUMMARY:\n`;
    if (this.selectedFile?.name) {
      summary += `File Name: ${this.selectedFile.name}\n`;
    }
    if (this.analysisResult.task_count) {
      summary += `Extracted Tasks Count: ${this.analysisResult.task_count}\n`;
    }
    const rep: any = this.analysisResult.report;
    if (typeof rep === 'string') {
      summary += `Report Summary:\n${rep.substring(0, 2000)}\n`;
    } else if (rep) {
      if (rep.executive_summary) {
        summary += `Executive Summary:\n${rep.executive_summary}\n`;
      }
      if (rep.analysis_overview) {
        const ov = rep.analysis_overview;
        summary += `Overview: Total Tasks=${ov.total_tasks}, Human=${ov.human_assignments}, AI=${ov.ai_assignments}, Total Cost=$${ov.total_estimated_cost}, High Risk=${ov.high_risk_tasks}\n`;
      }
    }
    return summary;
  }

  resetAnalysisState(): void {
    this.selectedFile = null;
    this.documentText = '';
    this.analysisResult = null;
    this.error = null;
    this.analyzing = false;
    this.currentStep = 0;
    this.progressPercent = 0;
    this.currentAgent = '';
    this.agentLogs = [];
    this.extractedTasksPreview = [];
    this.analysisTimestamp = 0;
  }


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

  analyzeDocumentStream(file?: File, text?: string): Observable<any> {
    return new Observable(observer => {
      const formData = new FormData();
      if (file) {
        formData.append('file', file);
      }
      
      const options: RequestInit = file 
        ? { method: 'POST', body: formData }
        : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ document_text: text }) };

      fetch(`${this.apiUrl}/task-routing/analyze/stream`, options)
        .then(response => {
          if (!response.ok) {
            throw new Error(`Server returned status ${response.status}`);
          }
          const reader = response.body?.getReader();
          const decoder = new TextDecoder('utf-8');
          let buffer = '';

          function readChunk() {
            reader?.read().then(({ done, value }) => {
              if (done) {
                observer.complete();
                return;
              }
              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split('\n\n');
              buffer = lines.pop() || '';

              for (const line of lines) {
                const trimmed = line.trim();
                if (trimmed.startsWith('data: ')) {
                  try {
                    const data = JSON.parse(trimmed.slice(6));
                    observer.next(data);
                  } catch (e) {
                    console.error('Failed to parse SSE data:', e);
                  }
                }
              }
              readChunk();
            }).catch(err => observer.error(err));
          }
          readChunk();
        })
        .catch(err => observer.error(err));
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
