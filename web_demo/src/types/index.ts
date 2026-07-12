export interface PredictionResult {
  id: string;
  text: string;
  prediction: 'depression' | 'normal';
  confidence: number;
  topic?: string;
  riskLevel: 'low' | 'medium' | 'high';
  timestamp: Date;
  modelName?: string;
  explanation?: string;
  highlightedKeywords?: string[];
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
  /** In-domain F1 (same as macroF1 for our models) */
  in_domain_f1: number;
  /** Cross-domain F1 (VSMEC) */
  cross_domain_f1: number;
  /** Standard deviation across seeds (if multi-seed) */
  std_in?: number;
  std_cross?: number;
  /** Model family */
  model_type: 'baseline' | 'bilstm' | 'phobert' | 'bertopic' | 'hybrid';
  /** Special badge label */
  note?: string;
}

export interface DashboardStats {
  totalComments: number;
  totalPredictions: number;
  currentModel: string;
  trainingDate: string;
  metrics: ModelMetrics;
}

export interface DashboardStatsExt {
  totalComments: number;
  totalPredictions: number;
  goldLabels: number;
  currentModel: string;
  bestCrossDomain: string;
  trainingDate: string;
  round: string;
  metrics: {
    accuracy: number;
    macroF1: number;
    weightedF1: number;
    precision: number;
    recall: number;
  };
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

export interface HistoryEntry {
  id: string;
  text: string;
  prediction: 'depression' | 'normal';
  confidence: number;
  topic?: string;
  risk_level: 'low' | 'medium' | 'high';
  model_name?: string;
  created_at: string;
}

export interface HistoryListResponse {
  items: HistoryEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface StatisticsResponse {
  confusion_matrix: number[][];
  class_distribution: { depression: number; normal: number };
  dataset_breakdown: { gold: number; pseudo: number };
  prediction_stats: {
    total: number;
    depression_count: number;
    normal_count: number;
    avg_confidence: number;
    unique_topics: number;
  };
}

export interface RefreshStatus {
  status: 'idle' | 'loading' | 'error';
  last_refresh: string | null;
  round: string | null;
}
