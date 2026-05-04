import { Component, OnInit } from '@angular/core';
import { ChatService } from '../../services/chat.service';
import { Knowledge } from '../../models/knowledge';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  knowledges: Knowledge[] = [];
  
  // Form properties
  newQuestion = '';
  newAnswer = '';
  editingId: number | null = null;

  isLoading = false;

  constructor(private chatService: ChatService) {}

  ngOnInit(): void {
    this.loadKnowledges();
  }

  loadKnowledges() {
    this.isLoading = true;
    this.chatService.getKnowledgeBase().subscribe(data => {
      this.knowledges = data;
      this.isLoading = false;
    });
  }

  saveKnowledge() {
    if (!this.newQuestion || !this.newAnswer) return;

    this.isLoading = true;
    if (this.editingId) {
      this.chatService.updateKnowledge(this.editingId, { question: this.newQuestion, answer: this.newAnswer })
        .subscribe(() => {
          this.resetForm();
          this.loadKnowledges();
        });
    } else {
      this.chatService.addKnowledge({ question: this.newQuestion, answer: this.newAnswer })
        .subscribe(() => {
          this.resetForm();
          this.loadKnowledges();
        });
    }
  }

  editKnowledge(k: Knowledge) {
    if (k.id) {
      this.editingId = k.id;
      this.newQuestion = k.question;
      this.newAnswer = k.answer;
    }
  }

  deleteKnowledge(id: number | undefined) {
    if (id) {
      this.isLoading = true;
      this.chatService.deleteKnowledge(id).subscribe(() => {
        this.loadKnowledges();
      });
    }
  }

  resetForm() {
    this.editingId = null;
    this.newQuestion = '';
    this.newAnswer = '';
  }
}
