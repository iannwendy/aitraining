import { useEffect, useState } from 'react';
import { getAdminStats } from '@/services/api';

interface AdminStats {
  total_users: number;
  total_predictions: number;
  predictions_by_user: Array<{
    username: string;
    pred_count: number;
  }>;
  recent_predictions: Array<{
    id: string;
    text: string;
    prediction: string;
    confidence: number;
    username?: string;
    created_at: string;
  }>;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getAdminStats();
        setStats(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load stats');
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="p-4 text-red-500 bg-red-100 rounded">{error}</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-foreground">Admin Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-card p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold text-muted-foreground">Total Users</h2>
          <p className="text-3xl font-bold text-foreground">{stats?.total_users ?? 0}</p>
        </div>
        <div className="bg-card p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold text-muted-foreground">Total Predictions</h2>
          <p className="text-3xl font-bold text-foreground">{stats?.total_predictions ?? 0}</p>
        </div>
      </div>

      {stats?.predictions_by_user && stats.predictions_by_user.length > 0 && (
        <div className="bg-card p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold text-foreground mb-4">Predictions by User</h2>
          <ul className="space-y-2">
            {stats.predictions_by_user.map((item) => (
              <li key={item.username} className="flex justify-between text-foreground">
                <span>{item.username}</span>
                <span className="font-medium">{item.pred_count}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {stats?.recent_predictions && stats.recent_predictions.length > 0 && (
        <div className="bg-card p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold text-foreground mb-4">Recent Predictions</h2>
          <ul className="space-y-3">
            {stats.recent_predictions.slice(0, 10).map((pred) => (
              <li key={pred.id} className="border-b pb-2 last:border-0">
                <div className="flex justify-between items-start">
                  <p className="text-sm text-foreground truncate max-w-md">{pred.text}</p>
                  <span
                    className={`text-xs px-2 py-1 rounded ${
                      pred.prediction === 'depression'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-green-100 text-green-700'
                    }`}
                  >
                    {pred.prediction}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">
                  {pred.username && <span className="mr-2">by {pred.username}</span>}
                  <span>Confidence: {(pred.confidence * 100).toFixed(1)}%</span>
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
