export interface Message {
  id?: number;
  text: string;
  sender: 'STUDENT' | 'BOT';
  timestamp?: Date;
  degraded?: boolean;  // true when answer came from V1 fallback (NLP unavailable)
}

export interface BotResponse {
  answer: string;
  degraded?: boolean;  // true when Flask NLP was unavailable and V1 keyword search was used
}
