import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { ChatSession, ChatMessage, VoiceRequest, OCRRequest } from '../models/task-routing.model';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = '/api';
  private currentSessionSubject = new BehaviorSubject<ChatSession | null>(null);
  public currentSession$ = this.currentSessionSubject.asObservable();

  constructor(private http: HttpClient) {}

  // ========== Chat Session Management ==========

  startSession(context?: any): Observable<{ success: boolean; session_id: string }> {
    return this.http.post<{ success: boolean; session_id: string }>(
      `${this.apiUrl}/chat/start`,
      { context }
    );
  }

  sendMessage(sessionId: string, message: string, image?: string): Observable<{
    success: boolean;
    response: string;
    tool_calls?: any[];
  }> {
    return this.http.post<{
      success: boolean;
      response: string;
      tool_calls?: any[];
    }>(`${this.apiUrl}/chat/message`, {
      session_id: sessionId,
      message: message,
      image: image
    });
  }

  getHistory(sessionId: string): Observable<{
    success: boolean;
    messages: ChatMessage[];
  }> {
    return this.http.get<{
      success: boolean;
      messages: ChatMessage[];
    }>(`${this.apiUrl}/chat/history/${sessionId}`);
  }

  clearSession(sessionId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/chat/session/${sessionId}`);
  }

  // ========== Voice Integration ==========

  speechToText(audioData: string, format: string = 'wav'): Observable<{
    success: boolean;
    text: string;
  }> {
    return this.http.post<{
      success: boolean;
      text: string;
    }>(`${this.apiUrl}/voice/speech-to-text`, {
      audio_data: audioData,
      format: format
    });
  }

  textToSpeech(text: string): Observable<{
    success: boolean;
    audio_data: string;
    format: string;
  }> {
    return this.http.post<{
      success: boolean;
      audio_data: string;
      format: string;
    }>(`${this.apiUrl}/voice/text-to-speech`, {
      text: text
    });
  }

  // ========== OCR Integration ==========

  extractText(imageData: string, format: string = 'png'): Observable<{
    success: boolean;
    text: string;
    confidence?: number;
  }> {
    return this.http.post<{
      success: boolean;
      text: string;
      confidence?: number;
    }>(`${this.apiUrl}/ocr/extract`, {
      image_data: imageData,
      format: format
    });
  }

  // ========== Local State Management ==========

  private activeSessionId: string | null = null;
  private activeMessages: ChatMessage[] = [];
  private loadedAnalysisTimestamp: number = 0;

  getActiveSessionId(): string | null {
    return this.activeSessionId;
  }

  getActiveMessages(): ChatMessage[] {
    return this.activeMessages;
  }

  getLoadedAnalysisTimestamp(): number {
    return this.loadedAnalysisTimestamp;
  }

  setActiveSession(sessionId: string, messages: ChatMessage[], analysisTimestamp: number = 0): void {
    this.activeSessionId = sessionId;
    this.activeMessages = messages;
    this.loadedAnalysisTimestamp = analysisTimestamp;
    this.setCurrentSession({
      session_id: sessionId,
      messages: messages
    });
  }

  addMessageToActiveSession(message: ChatMessage): void {
    this.activeMessages.push(message);
    this.addMessageToCurrentSession(message);
  }

  clearActiveSession(): void {
    this.activeSessionId = null;
    this.activeMessages = [];
    this.loadedAnalysisTimestamp = 0;
    this.clearCurrentSession();
  }

  setCurrentSession(session: ChatSession): void {
    this.currentSessionSubject.next(session);
  }

  getCurrentSession(): ChatSession | null {
    return this.currentSessionSubject.value;
  }

  addMessageToCurrentSession(message: ChatMessage): void {
    const current = this.currentSessionSubject.value;
    if (current) {
      current.messages.push(message);
      this.currentSessionSubject.next(current);
    }
  }

  clearCurrentSession(): void {
    this.currentSessionSubject.next(null);
  }
}

