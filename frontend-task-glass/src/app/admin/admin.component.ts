import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { AuthService } from '../services/auth.service';
import { environment } from '../../environments/environment';

interface ExpertAnalysis {
  id: number;
  key: string;
  data: string;
  created_at: string;
  updated_at: string;
}

interface RAGStats {
  total_chunks: number;
  total_documents: number;
  documents: any[];
}

@Component({
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.scss']
})
export class AdminComponent implements OnInit {
  private apiUrl = environment.apiUrl;
  
  // Tabs
  activeTab: 'rag' | 'expert' = 'rag';
  
  // RAG Management
  ragStats: RAGStats | null = null;
  selectedFile: File | null = null;
  isUploading = false;
  uploadMessage = '';
  
  // Expert Analysis Management
  expertAnalyses: ExpertAnalysis[] = [];
  newAnalysis = { key: '', data: '' };
  editingAnalysis: ExpertAnalysis | null = null;
  isLoadingExperts = false;
  expertMessage = '';

  @ViewChild('ragFileInput') ragFileInput!: ElementRef;

  constructor(
    private authService: AuthService,
    private http: HttpClient,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadRAGStats();
    this.loadExpertAnalyses();
  }

  // Auth Methods
  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  goHome(): void {
    this.router.navigate(['/']);
  }

  // RAG Management Methods
  loadRAGStats(): void {
    const headers = this.authService.getAuthHeaders();
    this.http.get<any>(`${this.apiUrl}/admin/rag/stats`, { headers }).subscribe({
      next: (response) => {
        if (response.success) {
          this.ragStats = response.stats;
        }
      },
      error: (error) => console.error('Failed to load RAG stats:', error)
    });
  }

  onFileSelected(event: any): void {
    this.selectedFile = event.target.files[0];
    this.uploadMessage = '';
  }

  uploadDocument(): void {
    if (!this.selectedFile) {
      this.uploadMessage = 'Please select a file first';
      return;
    }

    console.log('Uploading file:', this.selectedFile.name, 'Size:', this.selectedFile.size);
    this.isUploading = true;
    this.uploadMessage = 'Uploading and processing document...';

    const formData = new FormData();
    formData.append('file', this.selectedFile);

    const token = this.authService.getToken();
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`
    });

    this.http.post<any>(`${this.apiUrl}/admin/rag/upload`, formData, { headers }).subscribe({
      next: (response) => {
        console.log('Upload response:', response);
        this.isUploading = false;
        if (response.success) {
          this.uploadMessage = `✓ ${response.message}`;
          this.selectedFile = null;
          if (this.ragFileInput) {
            this.ragFileInput.nativeElement.value = '';
          }
          this.loadRAGStats();
        } else {
          this.uploadMessage = `✗ ${response.message || response.error || 'Upload failed'}`;
        }
      },
      error: (error) => {
        console.error('Upload error:', error);
        this.isUploading = false;
        const errorMsg = error.error?.message || error.error?.error || error.message || 'Upload failed - backend connection error';
        this.uploadMessage = `✗ ${errorMsg}`;
      }
    });
  }

  reloadNews(): void {
    const headers = this.authService.getAuthHeaders();
    this.http.post<any>(`${this.apiUrl}/admin/rag/reload-news`, {}, { headers }).subscribe({
      next: (response) => {
        if (response.success) {
          alert('News reloaded successfully!');
          this.loadRAGStats();
        }
      },
      error: (error) => alert('Failed to reload news: ' + error.error?.error)
    });
  }

  // Expert Analysis Methods
  loadExpertAnalyses(): void {
    this.isLoadingExperts = true;
    const headers = this.authService.getAuthHeaders();
    this.http.get<any>(`${this.apiUrl}/admin/expert-analysis`, { headers }).subscribe({
      next: (response) => {
        this.isLoadingExperts = false;
        if (response.success) {
          this.expertAnalyses = response.analyses;
        }
      },
      error: (error) => {
        this.isLoadingExperts = false;
        console.error('Failed to load expert analyses:', error);
      }
    });
  }

  addExpertAnalysis(): void {
    if (!this.newAnalysis.key || !this.newAnalysis.data) {
      this.expertMessage = 'Please fill in both ticker symbol and analysis';
      return;
    }

    const headers = this.authService.getAuthHeaders();
    const payload = {
      key: this.newAnalysis.key.trim(),
      data: this.newAnalysis.data.trim()
    };
    
    console.log('Sending expert analysis:', payload);
    console.log('With headers:', headers);
    
    this.http.post<any>(`${this.apiUrl}/admin/expert-analysis`, payload, { headers }).subscribe({
      next: (response) => {
        console.log('Success response:', response);
        if (response.success) {
          this.expertMessage = '✓ Expert analysis added successfully';
          this.newAnalysis = { key: '', data: '' };
          this.loadExpertAnalyses();
        } else {
          this.expertMessage = `✗ ${response.error || 'Failed to add analysis'}`;
        }
      },
      error: (error) => {
        console.error('Error response:', error);
        console.error('Error body:', error.error);
        this.expertMessage = `✗ ${error.error?.error || error.error?.msg || JSON.stringify(error.error) || 'Failed to add analysis'}`;
      }
    });
  }

  deleteExpertAnalysis(id: number): void {
    if (!confirm('Are you sure you want to delete this expert analysis?')) {
      return;
    }

    const headers = this.authService.getAuthHeaders();
    this.http.delete<any>(`${this.apiUrl}/admin/expert-analysis/${id}`, { headers }).subscribe({
      next: (response) => {
        if (response.success) {
          this.loadExpertAnalyses();
        }
      },
      error: (error) => alert('Failed to delete: ' + error.error?.error)
    });
  }
}
