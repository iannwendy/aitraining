import {
  PredictionResult,
  DashboardStatsExt,
  Topic,
  ModelComparison,
  HistoryListResponse,
  StatisticsResponse,
  RefreshStatus,
} from '@/types';

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
    throw new Error(`API Error ${response.status}: ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

// ── Dashboard ───────────────────────────────────────────────────────────────

export async function getDashboardStats(): Promise<DashboardStatsExt> {
  return fetchJSON<DashboardStatsExt>(`${API_BASE}/dashboard/stats`);
}

// ── Prediction ─────────────────────────────────────────────────────────────

export async function predict(text: string): Promise<PredictionResult> {
  return fetchJSON<PredictionResult>(`${API_BASE}/predict`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
}

export async function batchPredict(
  comments: string[],
): Promise<{
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

// ── Topics ────────────────────────────────────────────────────────────────

export async function getTopics(limit = 20): Promise<Topic[]> {
  return fetchJSON<Topic[]>(`${API_BASE}/topics?limit=${limit}`);
}

// ── Model Comparison ────────────────────────────────────────────────────────

export async function getModelComparison(): Promise<{ models: ModelComparison[] }> {
  return fetchJSON<{ models: ModelComparison[] }>(`${API_BASE}/models/comparison`);
}

// ── Statistics ─────────────────────────────────────────────────────────────

export async function getStatistics(): Promise<StatisticsResponse> {
  return fetchJSON<StatisticsResponse>(`${API_BASE}/statistics`);
}

// ── History ────────────────────────────────────────────────────────────────

export async function getHistory(
  limit = 50,
  offset = 0,
): Promise<HistoryListResponse> {
  return fetchJSON<HistoryListResponse>(
    `${API_BASE}/history?limit=${limit}&offset=${offset}`,
  );
}

export async function deleteHistoryEntry(id: string): Promise<void> {
  await fetchJSON(`${API_BASE}/history/${id}`, { method: 'DELETE' });
}

// ── Model Refresh (Hot-reload) ─────────────────────────────────────────────

export async function getRefreshStatus(): Promise<RefreshStatus> {
  return fetchJSON<RefreshStatus>(`${API_BASE}/models/refresh/status`);
}

export async function triggerRefresh(): Promise<{
  status: string;
  last_refresh: string | null;
  round: string | null;
  model_count: number;
}> {
  return fetchJSON(`${API_BASE}/models/refresh`, { method: 'POST' });
}
