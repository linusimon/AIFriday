import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Holding, EnrichedHolding, TotalStats } from '../models/market.model';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  /**
   * Load latest general market news into FAISS database
   */
  loadNews(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/news`);
  }

  /**
   * Upload a portfolio file (PDF, CSV, JSON, XML) for parsing and cleansing
   */
  uploadPortfolio(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<any>(`${this.apiUrl}/upload`, formData);
  }

  /**
   * Analyze parsed holdings to enrich with live quotes & sentiment, and generate risk summary
   */
  analyzePortfolio(holdings: Holding[]): Observable<any> {
    const headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    return this.http.post<any>(`${this.apiUrl}/analyze`, { holdings }, { headers });
  }

  /**
   * Interactive chat session with portfolio data, history, and optional image for OCR
   */
  chat(message: string, history: any[], imageBase64?: string | null, holdings?: EnrichedHolding[]): Observable<any> {
    const headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    const payload = {
      message,
      history,
      image: imageBase64,
      holdings
    };
    return this.http.post<any>(`${this.apiUrl}/chat`, payload, { headers });
  }

  /**
   * Get list of currently loaded general market news documents in vector db
   */
  getDocuments(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/documents`);
  }

  /**
   * Clear loaded documents in the RAG vector store
   */
  clearDocuments(): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/documents/clear`);
  }
}
