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

  // Image & Vision Attachments
  attachedImageBase64: string | null = null;
  attachedImageName: string = '';

  // Voice & Speech Integration
  isListening: boolean = false;
  isTtsEnabled: boolean = true;
  isPlayingSpeech: boolean = false;
  private recognition: any = null;

  constructor(private chatService: ChatService) {}

  ngOnInit(): void {
    this.startNewSession();
    this.initSpeechRecognition();
  }

  initSpeechRecognition(): void {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = false;
      this.recognition.lang = 'en-US';

      this.recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        this.userMessage = (this.userMessage ? this.userMessage + ' ' : '') + transcript;
        this.isListening = false;
      };

      this.recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        this.isListening = false;
      };

      this.recognition.onend = () => {
        this.isListening = false;
      };
    }
  }

  toggleListening(): void {
    if (!this.recognition) {
      alert('Speech Recognition (STT) is not supported in this browser. Please use Google Chrome or Microsoft Edge.');
      return;
    }

    if (this.isListening) {
      this.recognition.stop();
      this.isListening = false;
    } else {
      this.isListening = true;
      this.recognition.start();
    }
  }

  speak(text: string): void {
    if (!this.isTtsEnabled) return;
    
    window.speechSynthesis.cancel();
    
    let cleanText = text
      .replace(/[\*#`>|\[\]\(-]/g, ' ')
      .replace(/(\r\n|\n|\r)/gm, ' ')
      .trim();
      
    if (cleanText.length > 250) {
      cleanText = cleanText.substring(0, 250) + '... and more details are available in the task matrix.';
    }

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.onstart = () => {
      this.isPlayingSpeech = true;
    };
    utterance.onend = () => {
      this.isPlayingSpeech = false;
    };
    utterance.onerror = () => {
      this.isPlayingSpeech = false;
    };

    window.speechSynthesis.speak(utterance);
  }

  stopSpeech(): void {
    window.speechSynthesis.cancel();
    this.isPlayingSpeech = false;
  }

  onImageSelected(event: any): void {
    if (event.target.files && event.target.files.length > 0) {
      const file = event.target.files[0];
      this.attachedImageName = file.name;
      
      const reader = new FileReader();
      reader.onload = () => {
        this.attachedImageBase64 = reader.result as string;
      };
      reader.readAsDataURL(file);
    }
  }

  clearImageAttachment(): void {
    this.attachedImageBase64 = null;
    this.attachedImageName = '';
  }

  startNewSession(): void {
    this.loading = true;
    this.chatService.startSession().subscribe({
      next: (response: any) => {
        this.sessionId = response.session_id;
        this.messages = [{
          role: 'assistant',
          content: 'Hello! I\'m your AI Task Routing Assistant. I can analyze architecture diagrams, speak responses aloud, process voice inputs, and help answer questions about resource assignments, SLA risks, and cost models. How can I help you today?',
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
    if ((!this.userMessage.trim() && !this.attachedImageBase64) || !this.sessionId) {
      return;
    }

    const userText = this.userMessage;
    const userImage = this.attachedImageBase64;

    const userMsg: ChatMessage = {
      role: 'user',
      content: userText,
      image: userImage || undefined,
      timestamp: new Date()
    };
    
    this.messages.push(userMsg);
    this.userMessage = '';
    this.clearImageAttachment();
    this.loading = true;
    this.scrollToBottom();

    this.chatService.sendMessage(this.sessionId, userText, userImage || undefined).subscribe({
      next: (response: any) => {
        const assistantMsg: ChatMessage = {
          role: 'assistant',
          content: response.response,
          timestamp: new Date()
        };
        this.messages.push(assistantMsg);
        this.loading = false;
        this.scrollToBottom();
        this.speak(response.response);
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
