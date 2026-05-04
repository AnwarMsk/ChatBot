import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { delay } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { Message, BotResponse } from '../models/message';
import { Knowledge } from '../models/knowledge';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = environment.apiUrl;
  
  // Mock data for Admin Dashboard
  private mockKnowledges: Knowledge[] = [
    { id: 1, question: 'Quelles sont les heures d\'ouverture de la bibliothèque ?', answer: 'La bibliothèque est ouverte de 8h à 20h du lundi au vendredi.' },
    { id: 2, question: 'Comment puis-je m\'inscrire aux cours ?', answer: 'L\'inscription se fait via l\'intranet étudiant dans la section "Scolarité".' }
  ];

  constructor(private http: HttpClient) { }

  // Chatbot methods
  askQuestion(text: string): Observable<BotResponse> {
    const payload = { question: text };
    return this.http.post<BotResponse>('/api/chatbot/ask', payload);
  }

  // Admin CRUD methods (Mocked for now)
  getKnowledgeBase(): Observable<Knowledge[]> {
    return of(this.mockKnowledges).pipe(delay(500));
  }

  addKnowledge(knowledge: Knowledge): Observable<Knowledge> {
    const newKnowledge = { ...knowledge, id: this.mockKnowledges.length + 1 };
    this.mockKnowledges.push(newKnowledge);
    return of(newKnowledge).pipe(delay(500));
  }

  updateKnowledge(id: number, knowledge: Knowledge): Observable<Knowledge> {
    const index = this.mockKnowledges.findIndex(k => k.id === id);
    if (index !== -1) {
      this.mockKnowledges[index] = { ...knowledge, id };
    }
    return of(this.mockKnowledges[index]).pipe(delay(500));
  }

  deleteKnowledge(id: number): Observable<boolean> {
    this.mockKnowledges = this.mockKnowledges.filter(k => k.id !== id);
    return of(true).pipe(delay(500));
  }
}
