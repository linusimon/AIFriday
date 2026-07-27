import { Component, OnInit } from '@angular/core';
import { ChatService } from '../services/chat.service';
import { ChatMessage } from '../models/task-routing.model';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent implements OnInit {
  sessionId: string | null = null;
  messages: ChatMessage[] = [];
  userMessage: string = '';
  loading: boolean = false;
  error: string | null = null;

  constructor(private chatService: ChatService) {}

  ngOnInit(): void {
    this.startNewSession();
  }

  startNewSession(): void {
    this.loading = true;
    this.chatService.startSession().subscribe({
      next: (response: any) => {
        this.sessionId = response.session_id;
        this.messages = [{
          role: 'assistant',
          content: 'Hello! I\'m your AI assistant for task routing. I can help you understand routing decisions, explore alternatives, and answer questions about resource assignments. How can I help you today?',
          timestamp: new Date()
        }];
        this.loading = false;
      },
      error: (err: any) => {
        this.error = 'Failed to start chat session. Please try again.';
        this.loading = false;
        console.error('Chat session error:', err);
      }
    });
  }

  sendMessage(): void {
    if (!this.userMessage.trim() || !this.sessionId) {
      return;
    }

    const userMsg: ChatMessage = {
      role: 'user',
      content: this.userMessage,
      timestamp: new Date()
    };
    
    this.messages.push(userMsg);
    const messageText = this.userMessage;
    this.userMessage = '';
    this.loading = true;

    this.chatService.sendMessage(this.sessionId, messageText).subscribe({
      next: (response: any) => {
        const assistantMsg: ChatMessage = {
          role: 'assistant',
          content: response.response,
          timestamp: new Date()
        };
        this.messages.push(assistantMsg);
        this.loading = false;
        this.scrollToBottom();
      },
      error: (err: any) => {
        this.error = 'Failed to send message. Please try again.';
        this.loading = false;
        console.error('Chat message error:', err);
      }
    });
  }

  clearChat(): void {
    if (this.sessionId) {
      this.chatService.clearSession(this.sessionId).subscribe();
    }
    this.startNewSession();
  }

  scrollToBottom(): void {
    setTimeout(() => {
      const chatContainer = document.querySelector('.messages-container');
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    }, 100);
  }

  onKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }
}
