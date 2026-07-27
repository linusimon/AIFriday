export interface Holding {
  symbol: string;
  name: string;
  shares: number;
  purchasePrice: number;
}

export interface EnrichedHolding {
  symbol: string;
  name: string;
  shares: number;
  purchasePrice: number;
  costBasis: number;
  currentPrice: number;
  currentValue: number;
  dailyChange: number;
  dailyChangePercent: number;
  sentiment: {
    bullishPercent: number;
    bearishPercent: number;
  };
  sentimentScore: number;
  news: Array<{
    headline: string;
    summary: string;
    source: string;
    url: string;
  }>;
}

export interface TotalStats {
  costBasis: number;
  currentValue: number;
  gainLoss: number;
  gainLossPercent: number;
  dailyChange: number;
  dailyChangePercent: number;
}

export interface ChatMessage {
  sender: 'user' | 'assistant';
  text: string;
  timestamp: Date;
  image?: string; // base64 representation if attached
  isSpeech?: boolean;
}
