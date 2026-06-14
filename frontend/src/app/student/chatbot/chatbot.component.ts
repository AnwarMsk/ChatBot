import { Component, OnInit, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { ChatService } from '../../services/chat.service';
import { Message } from '../../models/message';

@Component({
  selector: 'app-chatbot',
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.css']
})
export class ChatbotComponent implements OnInit, AfterViewChecked {
  @ViewChild('scrollMe') private myScrollContainer!: ElementRef;
  @ViewChild('messageInput') messageInput!: ElementRef;

  messages: Message[] = [];
  newMessageText: string = '';
  isTyping: boolean = false;

  constructor(private chatService: ChatService) {}

  ngOnInit(): void {
    // Welcome message
    this.messages.push({
      text: 'Bonjour ! Je suis l\'assistant virtuel de l\'EMI. Comment puis-je vous aider aujourd\'hui ?',
      sender: 'BOT',
      timestamp: new Date()
    });
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  scrollToBottom(): void {
    try {
      this.myScrollContainer.nativeElement.scrollTop = this.myScrollContainer.nativeElement.scrollHeight;
    } catch (err) {}
  }

  sendMessage(): void {
    if (!this.newMessageText.trim()) return;

    // Add student message
    const userMessage: Message = {
      text: this.newMessageText,
      sender: 'STUDENT',
      timestamp: new Date()
    };
    this.messages.push(userMessage);
    
    const query = this.newMessageText;
    this.newMessageText = '';
    
    // Focus back on input
    setTimeout(() => this.messageInput.nativeElement.focus(), 0);

    // Show typing indicator
    this.isTyping = true;
    this.scrollToBottom();

    // Call service (mocked delay 1500)
    this.chatService.askQuestion(query).subscribe({
      next: (response) => {
        this.isTyping = false;
        this.messages.push({
          text: response.answer,
          sender: 'BOT',
          timestamp: new Date(),
          degraded: response.degraded ?? false
        });
      },
      error: (err) => {
        this.isTyping = false;
        this.messages.push({
          text: 'Désolé, une erreur est survenue lors de la communication avec le serveur (Backend Java).',
          sender: 'BOT',
          timestamp: new Date()
        });
      }
    });
  }
}
