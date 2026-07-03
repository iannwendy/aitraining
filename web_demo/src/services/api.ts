import { PredictionResult, DashboardStats, Topic, ModelComparison } from '@/types';

const API_BASE = '/api';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }

  return response.json();
}

// Dashboard
export async function getDashboardStats(): Promise<DashboardStats> {
  return fetchJSON(`${API_BASE}/dashboard/stats`);
}

// Prediction
export async function predict(text: string): Promise<PredictionResult> {
  return fetchJSON(`${API_BASE}/predict`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
}

// Batch Prediction
export async function batchPredict(comments: string[]): Promise<{
  results: PredictionResult[];
  total: number;
  depression_count: number;
  normal_count: number;
}> {
  return fetchJSON(`${API_BASE}/predict/batch`, {
    method: 'POST',
    body: JSON.stringify({ comments }),
  });
}

// Topics
export async function getTopics(): Promise<Topic[]> {
  return fetchJSON(`${API_BASE}/topics`);
}

// Model Comparison
export async function getModelComparison(): Promise<{ models: ModelComparison[] }> {
  return fetchJSON(`${API_BASE}/models/comparison`);
}
