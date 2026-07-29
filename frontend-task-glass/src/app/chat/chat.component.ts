import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { ChatService } from '../services/chat.service';
import { TaskRoutingService } from '../services/task-routing.service';
import { ChatMessage } from '../models/task-routing.model';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent implements OnInit {
  @Input() isFloating: boolean = false;
  @Output() closeChat = new EventEmitter<void>();

  sessionId: string | null = null;
  messages: ChatMessage[] = [];
  userMessage: string = '';
  loading: boolean = false;
  error: string | null = null;
  activeAnalysisFileName: string | null = null;

  // Image & Vision Attachments
  attachedImageBase64: string | null = null;
  attachedImageName: string = '';

  // Voice & Speech Integration
  isListening: boolean = false;
  isTtsEnabled: boolean = true;
  isPlayingSpeech: boolean = false;
  private recognition: any = null;

  onCloseClick(): void {
    this.closeChat.emit();
  }

  constructor(
    private chatService: ChatService,
    public taskRoutingService: TaskRoutingService
  ) {}

  ngOnInit(): void {
    const activeSessionId = this.chatService.getActiveSessionId();
    const activeMessages = this.chatService.getActiveMessages();
    const currentAnalysisTimestamp = this.taskRoutingService.analysisTimestamp;
    const loadedAnalysisTimestamp = this.chatService.getLoadedAnalysisTimestamp();

    if (this.taskRoutingService.analysisResult) {
      this.activeAnalysisFileName = this.taskRoutingService.selectedFile?.name || 'Uploaded Document';
    } else {
      this.activeAnalysisFileName = null;
    }

    if (activeSessionId && activeMessages.length > 0 && currentAnalysisTimestamp === loadedAnalysisTimestamp) {
      this.sessionId = activeSessionId;
      this.messages = activeMessages;
    } else {
      this.startNewSession();
    }

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
    const analysisContext = this.taskRoutingService.getAnalysisContextSummary();
    const fileName = this.taskRoutingService.selectedFile?.name || (this.taskRoutingService.analysisResult ? 'Uploaded Document' : null);
    this.activeAnalysisFileName = fileName;

    const contextPayload = analysisContext ? { document_analysis: analysisContext } : undefined;

    this.chatService.startSession(contextPayload).subscribe({
      next: (response: any) => {
        this.sessionId = response.session_id;

        let initialGreeting = "Hello! I'm your AI Task Routing Assistant. I can analyze architecture diagrams, speak responses aloud, process voice inputs, and help answer questions about resource assignments, SLA risks, and cost models. How can I help you today?";

        if (fileName && this.taskRoutingService.analysisResult) {
          initialGreeting = `Hello! I have loaded the document analysis details for **${fileName}** (${this.taskRoutingService.analysisResult.task_count || 0} tasks identified). I am ready to provide assistance, answer questions, or explain routing decisions, SLA risks, and cost recommendations based on this analysis. How can I help you today?`;
        }

        this.messages = [{
          role: 'assistant',
          content: initialGreeting,
          timestamp: new Date()
        }];

        if (this.sessionId) {
          this.chatService.setActiveSession(this.sessionId, this.messages, this.taskRoutingService.analysisTimestamp);
        }
        this.loading = false;
      },
      error: (err: any) => {
        this.error = 'Failed to start chat session. Please try again.';
        this.loading = false;
        console.error('Chat session error:', err);
      }
    });
  }

  // Accordion state for Chat Guardrail & Audit Logs
  expandedLogs: { [key: number]: boolean } = {};

  toggleLog(index: number): void {
    this.expandedLogs[index] = !this.expandedLogs[index];
  }

  getObjectKeys(obj: any): string[] {
    return obj ? Object.keys(obj) : [];
  }

  formatJson(obj: any): string {
    if (!obj) return '';
    try {
      return JSON.stringify(obj, null, 2);
    } catch {
      return String(obj);
    }
  }

  generatePlanFromChat(): void {
    this.loading = true;
    const chatDocName = this.activeAnalysisFileName || 'Chat Session';
    
    this.taskRoutingService.generateExecutionPlan({
      source: `Chat Assistant (${chatDocName})`,
      document_text: this.userMessage || this.taskRoutingService.documentText || 'Agile Task Analysis & Execution Plan'
    }).subscribe({
      next: (res: any) => {
        this.loading = false;
        this.messages.push({
          role: 'assistant',
          content: `🚀 I have created a new **Project Execution Plan** based on our session! It includes Agile User Stories, resource/agent assignments, effort points, and a multi-sprint roadmap timeline.\n\nYou can inspect it on the **Execution Plans** tab in the main navigation!`,
          timestamp: new Date()
        });
      },
      error: (err: any) => {
        this.loading = false;
        this.error = 'Failed to generate execution plan from chat.';
        console.error(err);
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
    if (this.sessionId) {
      this.chatService.setActiveSession(this.sessionId, this.messages, this.taskRoutingService.analysisTimestamp);
    }
    this.userMessage = '';
    this.clearImageAttachment();
    this.loading = true;
    this.scrollToBottom();

    let apiMessage = userText;
    const analysisSummary = this.taskRoutingService.getAnalysisContextSummary();
    if (analysisSummary && this.messages.filter(m => m.role === 'user').length === 1) {
      apiMessage = `[Document Analysis Context:\n${analysisSummary}]\n\nUser Question: ${userText}`;
    }

    this.chatService.sendMessage(this.sessionId, apiMessage, userImage || undefined).subscribe({
      next: (response: any) => {
        const textContent = response.response || response.message || 'No response content returned.';
        const assistantMsg: ChatMessage = {
          role: 'assistant',
          content: textContent,
          timestamp: new Date(),
          guardrail_report: response.guardrail_report,
          input_data: response.input_data
        };
        this.messages.push(assistantMsg);
        if (this.sessionId) {
          this.chatService.setActiveSession(this.sessionId, this.messages, this.taskRoutingService.analysisTimestamp);
        }
        this.loading = false;
        this.scrollToBottom();
        this.speak(textContent);
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
    this.chatService.clearActiveSession();
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
