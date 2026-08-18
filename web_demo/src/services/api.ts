import {
  PredictionResult,
  DashboardStatsExt,
  Topic,
  ModelComparison,
  HistoryListResponse,
  StatisticsResponse,
  RefreshStatus,
  User,
  AuthResponse,
  LoginCredentials,
  RegisterCredentials,
  AdminStats,
} from '@/types';

const API_BASE = '/api';

// API Configuration
const API_TIMEOUT = 30000; // 30 seconds timeout
const MAX_RETRIES = 1;

// Custom error types for better error handling
export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public isTimeout = false
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// Abort controller wrapper for timeout
function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeout: number
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  return fetch(url, {
    ...options,
    signal: controller.signal,
  })
    .finally(() => clearTimeout(timeoutId))
    .catch((error) => {
      if (error.name === 'AbortError') {
        throw new APIError('Request timed out', undefined, true);
      }
      throw error;
    });
}

// Fetch with retry logic
async function fetchWithRetry<T>(
  url: string,
  options: RequestInit,
  retries = MAX_RETRIES
): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetchWithTimeout(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      }, API_TIMEOUT);

      if (!response.ok) {
        // Try to parse error message from response
        let errorMessage = `API Error ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch {
          // Use default error message
        }
        throw new APIError(errorMessage, response.status);
      }

      return response.json() as Promise<T>;
    } catch (error) {
      lastError = error as Error;

      // Don't retry on timeout or client errors (4xx)
      if (
        error instanceof APIError &&
        (error.isTimeout || (error.status && error.status >= 400 && error.status < 500))
      ) {
        throw error;
      }

      // Wait before retry (exponential backoff)
      if (attempt < retries) {
        await new Promise((resolve) =>
          setTimeout(resolve, Math.pow(2, attempt) * 500)
        );
      }
    }
  }

  throw lastError || new APIError('Request failed after retries');
}

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  return fetchWithRetry<T>(url, options || {});
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
    headers: authHeaders(),
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
    headers: authHeaders(),
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

// ── Auth ─────────────────────────────────────────────────────────────────────

const TOKEN_KEY = 'auth_token';
const USER_KEY = 'auth_user';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getStoredUser(): User | null {
  const stored = localStorage.getItem(USER_KEY);
  if (!stored) return null;
  try {
    return JSON.parse(stored) as User;
  } catch {
    return null;
  }
}

export function setStoredUser(user: User): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function login(credentials: LoginCredentials): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(error.detail || 'Login failed');
  }

  const data = await response.json();
  setToken(data.access_token);
  setStoredUser(data.user);
  return data;
}

export async function register(credentials: RegisterCredentials): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Registration failed' }));
    throw new Error(error.detail || 'Registration failed');
  }

  const data = await response.json();
  setToken(data.access_token);
  setStoredUser(data.user);
  return data;
}

export async function logout(): Promise<void> {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      headers: authHeaders(),
    });
  } finally {
    removeToken();
  }
}

export async function getCurrentUser(): Promise<User> {
  const response = await fetch(`${API_BASE}/auth/me`, {
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    removeToken();
    throw new Error('Not authenticated');
  }

  const user = await response.json();
  setStoredUser(user);
  return user;
}

// ── Admin ─────────────────────────────────────────────────────────────────────

export async function getAdminStats(): Promise<AdminStats> {
  return fetchJSON<AdminStats>(`${API_BASE}/admin/stats`, {
    headers: authHeaders(),
  });
}

export async function getAdminUsers(): Promise<{ users: User[] }> {
  return fetchJSON<{ users: User[] }>(`${API_BASE}/admin/users`, {
    headers: authHeaders(),
  });
}
