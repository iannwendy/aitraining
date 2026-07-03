export interface PredictionResult {
  id: string;
  text: string;
  prediction: 'depression' | 'normal';
  confidence: number;
  topic?: string;
  riskLevel: 'low' | 'medium' | 'high';
  timestamp: Date;
}

export interface Topic {
  id: number;
  name: string;
  keywords: string[];
  count: number;
  percentage: number;
  examples: string[];
}

export interface ModelMetrics {
  accuracy: number;
  macroF1: number;
  weightedF1: number;
  precision: number;
  recall: number;
}

export interface ModelComparison {
  name: string;
  accuracy: number;
  macroF1: number;
  weightedF1: number;
  precision: number;
  recall: number;
}

export interface DashboardStats {
  totalComments: number;
  totalPredictions: number;
  currentModel: string;
  trainingDate: string;
  metrics: ModelMetrics;
}

export interface BatchPredictionResult {
  comment: string;
  prediction: 'depression' | 'normal';
  confidence: number;
  topic?: string;
}

export interface WordCloudItem {
  text: string;
  value: number;
  color?: string;
}
