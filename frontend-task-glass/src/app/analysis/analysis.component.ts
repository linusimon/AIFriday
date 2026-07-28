import { Component, OnInit } from '@angular/core';
import { TaskRoutingService } from '../services/task-routing.service';
import { AnalysisResult } from '../models/task-routing.model';

@Component({
  selector: 'app-analysis',
  templateUrl: './analysis.component.html',
  styleUrls: ['./analysis.component.css']
})
export class AnalysisComponent implements OnInit {
  selectedFile: File | null = null;
  documentText: string = '';
  analyzing: boolean = false;
  analysisResult: AnalysisResult | null = null;
  error: string | null = null;
  inputMode: 'file' | 'text' = 'file';
  activeResultTab: 'overview' | 'matrix' | 'recommendations' = 'overview';

  // Streaming & Async Progress State
  currentStep: number = 0;
  totalSteps: number = 7;
  progressPercent: number = 0;
  currentAgent: string = '';
  agentLogs: { agent: string; status: string; step: number; message: string; timestamp: string }[] = [];
  extractedTasksPreview: any[] = [];

  // Floating Chat Assistant Drawer State
  isChatOpen: boolean = false;
  isChatMinimized: boolean = false;
  isChatExpanded: boolean = false;

  constructor(public taskRoutingService: TaskRoutingService) {}

  toggleChat(): void {
    if (this.isChatMinimized) {
      this.isChatMinimized = false;
      this.isChatOpen = true;
    } else {
      this.isChatOpen = !this.isChatOpen;
    }
  }

  closeChat(): void {
    this.isChatOpen = false;
    this.isChatMinimized = false;
    this.isChatExpanded = false;
  }

  toggleMinimize(): void {
    this.isChatMinimized = !this.isChatMinimized;
  }

  toggleExpand(): void {
    this.isChatExpanded = !this.isChatExpanded;
    if (this.isChatExpanded) {
      this.isChatMinimized = false;
    }
  }

  ngOnInit(): void {
    // Restore persistent state from TaskRoutingService upon tab navigation
    this.selectedFile = this.taskRoutingService.selectedFile;
    this.documentText = this.taskRoutingService.documentText;
    this.inputMode = this.taskRoutingService.inputMode;
    this.activeResultTab = this.taskRoutingService.activeResultTab;
    this.analyzing = this.taskRoutingService.analyzing;
    this.analysisResult = this.taskRoutingService.analysisResult;
    this.error = this.taskRoutingService.error;
    this.currentStep = this.taskRoutingService.currentStep;
    this.totalSteps = this.taskRoutingService.totalSteps;
    this.progressPercent = this.taskRoutingService.progressPercent;
    this.currentAgent = this.taskRoutingService.currentAgent;
    this.agentLogs = [...this.taskRoutingService.agentLogs];
    this.extractedTasksPreview = [...this.taskRoutingService.extractedTasksPreview];
  }

  private syncStateToService(): void {
    this.taskRoutingService.selectedFile = this.selectedFile;
    this.taskRoutingService.documentText = this.documentText;
    this.taskRoutingService.inputMode = this.inputMode;
    this.taskRoutingService.activeResultTab = this.activeResultTab;
    this.taskRoutingService.analyzing = this.analyzing;
    this.taskRoutingService.analysisResult = this.analysisResult;
    this.taskRoutingService.error = this.error;
    this.taskRoutingService.currentStep = this.currentStep;
    this.taskRoutingService.totalSteps = this.totalSteps;
    this.taskRoutingService.progressPercent = this.progressPercent;
    this.taskRoutingService.currentAgent = this.currentAgent;
    this.taskRoutingService.agentLogs = [...this.agentLogs];
    this.taskRoutingService.extractedTasksPreview = [...this.extractedTasksPreview];
  }

  onFileSelected(event: any): void {
    const file = event.target.files[0];
    if (file) {
      // Check file type
      const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
      if (!allowedTypes.includes(file.type)) {
        this.error = 'Invalid file type. Please upload PDF, DOCX, or TXT file.';
        this.syncStateToService();
        return;
      }
      
      // Check file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        this.error = 'File too large. Maximum size is 10MB.';
        this.syncStateToService();
        return;
      }

      this.selectedFile = file;
      this.error = null;
      this.syncStateToService();
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      const file = files[0];
      this.selectedFile = file;
      this.error = null;
      this.syncStateToService();
    }
  }

  onTextChange(): void {
    this.syncStateToService();
  }

  setActiveResultTab(tab: 'overview' | 'matrix' | 'recommendations'): void {
    this.activeResultTab = tab;
    this.taskRoutingService.activeResultTab = tab;
  }

  analyzeDocument(): void {
    if (this.inputMode === 'file' && !this.selectedFile) {
      this.error = 'Please select a file to analyze.';
      this.syncStateToService();
      return;
    }

    if (this.inputMode === 'text' && !this.documentText.trim()) {
      this.error = 'Please enter document text to analyze.';
      this.syncStateToService();
      return;
    }

    this.analyzing = true;
    this.error = null;
    this.analysisResult = null;
    this.currentStep = 0;
    this.progressPercent = 5;
    this.currentAgent = 'Initializing Pipeline...';
    this.agentLogs = [];
    this.extractedTasksPreview = [];
    this.syncStateToService();

    const file = this.inputMode === 'file' ? this.selectedFile! : undefined;
    const text = this.inputMode === 'text' ? this.documentText : undefined;

    this.taskRoutingService.analyzeDocumentStream(file, text).subscribe({
      next: (data: any) => {
        if (data.type === 'progress') {
          this.currentStep = data.step || this.currentStep;
          this.totalSteps = data.total_steps || 7;
          this.progressPercent = Math.min(95, Math.round((this.currentStep / this.totalSteps) * 100));
          this.currentAgent = data.agent || '';

          let msg = `Agent ${data.agent} ${data.status}`;
          if (data.status === 'started') {
            msg = `Started execution for ${data.agent}`;
          } else if (data.status === 'completed') {
            msg = `Completed execution for ${data.agent}`;
          }

          this.agentLogs.unshift({
            agent: data.agent,
            status: data.status,
            step: data.step,
            message: msg,
            timestamp: new Date().toLocaleTimeString()
          });

          // Async Initial Task Data Fetch: Check if DocumentAnalysisAgent returned tasks
          if (data.agent === 'DocumentAnalysisAgent' && data.status === 'completed' && data.result?.extracted_tasks) {
            this.extractedTasksPreview = data.result.extracted_tasks;
            console.log('Initial extracted tasks available:', this.extractedTasksPreview);
          }
          this.syncStateToService();
        } else if (data.type === 'complete') {
          this.progressPercent = 100;
          this.analyzing = false;
          this.analysisResult = {
            success: true,
            analysis_complete: true,
            report: data.report,
            task_count: data.task_count,
            message: 'Task routing analysis completed successfully'
          } as any;
          this.taskRoutingService.analysisTimestamp = Date.now();
          this.syncStateToService();
          console.log('Analysis complete via Stream:', data);
        } else if (data.type === 'error') {
          this.analyzing = false;
          this.error = data.error || 'Analysis stream failed.';
          this.syncStateToService();
        }
      },
      error: (err: any) => {
        console.warn('Stream failed, falling back to standard API call...', err);
        // Fallback to sync endpoint if SSE fails
        const analyzeObservable = this.inputMode === 'file'
          ? this.taskRoutingService.analyzeDocument(this.selectedFile!)
          : this.taskRoutingService.analyzeDocumentText(this.documentText);

        analyzeObservable.subscribe({
          next: (result: any) => {
            this.analyzing = false;
            this.analysisResult = result;
            this.taskRoutingService.analysisTimestamp = Date.now();
            this.syncStateToService();
          },
          error: (fallbackErr: any) => {
            this.analyzing = false;
            this.error = fallbackErr.error?.message || 'Analysis failed. Please try again.';
            this.syncStateToService();
          }
        });
      }
    });
  }

  reset(): void {
    this.selectedFile = null;
    this.documentText = '';
    this.analysisResult = null;
    this.error = null;
    this.analyzing = false;
    this.currentStep = 0;
    this.progressPercent = 0;
    this.agentLogs = [];
    this.extractedTasksPreview = [];
    this.taskRoutingService.resetAnalysisState();
  }

  switchMode(mode: 'file' | 'text'): void {
    this.inputMode = mode;
    this.reset();
    this.taskRoutingService.inputMode = mode;
  }
}
