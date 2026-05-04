export interface Message {
  id?: number;
  text: string;
  sender: 'STUDENT' | 'BOT';
  timestamp?: Date;
}

export interface BotResponse {
  answer: string;
}
