import { Component } from '@angular/core';
import { TaskRoutingService } from '../services/task-routing.service';
import { AnalysisResult } from '../models/task-routing.model';

@Component({
  selector: 'app-analysis',
  templateUrl: './analysis.component.html',
  styleUrls: ['./analysis.component.css']
})
export class AnalysisComponent {
  selectedFile: File | null = null;
  documentText: string = '';
  analyzing: boolean = false;
  analysisResult: AnalysisResult | null = null;
  error: string | null = null;
  inputMode: 'file' | 'text' = 'file';

  constructor(private taskRoutingService: TaskRoutingService) {}

  onFileSelected(event: any): void {
    const file = event.target.files[0];
    if (file) {
      // Check file type
      const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
      if (!allowedTypes.includes(file.type)) {
        this.error = 'Invalid file type. Please upload PDF, DOCX, or TXT file.';
        return;
      }
      
      // Check file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        this.error = 'File too large. Maximum size is 10MB.';
        return;
      }

      this.selectedFile = file;
      this.error = null;
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
    }
  }

  analyzeDocument(): void {
    if (this.inputMode === 'file' && !this.selectedFile) {
      this.error = 'Please select a file to analyze.';
      return;
    }

    if (this.inputMode === 'text' && !this.documentText.trim()) {
      this.error = 'Please enter document text to analyze.';
      return;
    }

    this.analyzing = true;
    this.error = null;
    this.analysisResult = null;

    const analyzeObservable = this.inputMode === 'file'
      ? this.taskRoutingService.analyzeDocument(this.selectedFile!)
      : this.taskRoutingService.analyzeDocumentText(this.documentText);

    analyzeObservable.subscribe({
      next: (result: any) => {
        this.analyzing = false;
        this.analysisResult = result;
        console.log('Analysis complete:', result);
      },
      error: (err: any) => {
        this.analyzing = false;
        this.error = err.error?.message || 'Analysis failed. Please try again.';
        console.error('Analysis error:', err);
      }
    });
  }

  reset(): void {
    this.selectedFile = null;
    this.documentText = '';
    this.analysisResult = null;
    this.error = null;
    this.analyzing = false;
  }

  switchMode(mode: 'file' | 'text'): void {
    this.inputMode = mode;
    this.reset();
  }
}
