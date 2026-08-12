import { useState, useEffect } from 'react';
import { Users, MessageSquare, TrendingUp, Clock, AlertCircle } from 'lucide-react';
import { getAdminStats, getAdminUsers } from '@/services/api';
import { AdminStats, User } from '@/types';

export default function AdminDashboard() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    setError('');
    try {
      const [statsData, usersData] = await Promise.all([
        getAdminStats(),
        getAdminUsers(),
      ]);
      setStats(statsData);
      setUsers(usersData.users);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-red-600">
        <AlertCircle className="w-5 h-5 mb-2" />
        {error}
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Users',
      value: stats?.total_users || 0,
      icon: Users,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
    },
    {
      title: 'Total Predictions',
      value: stats?.total_predictions || 0,
      icon: MessageSquare,
      color: 'text-accent',
      bgColor: 'bg-accent/10',
    },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      <h1 className="font-display text-2xl font-bold text-dark">
        Admin Dashboard
      </h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {statCards.map((card) => (
          <div
            key={card.title}
            className="bg-white rounded-2xl p-6 shadow-lg border border-slate-100"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted mb-1">{card.title}</p>
                <p className="text-3xl font-bold text-dark">{card.value}</p>
              </div>
              <div className={`w-12 h-12 rounded-xl ${card.bgColor} flex items-center justify-center`}>
                <card.icon className={`w-6 h-6 ${card.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-2xl shadow-lg border border-slate-100 overflow-hidden">
        <div className="p-6 border-b border-slate-100">
          <h2 className="text-lg font-semibold text-dark flex items-center gap-2">
            <Users className="w-5 h-5 text-primary" />
            Users
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                  Username
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                  Created
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="font-medium text-dark">{user.username}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded-full ${
                        user.role === 'admin'
                          ? 'bg-accent/10 text-accent'
                          : 'bg-slate-100 text-muted'
                      }`}
                    >
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-muted">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Predictions by User */}
      <div className="bg-white rounded-2xl shadow-lg border border-slate-100 overflow-hidden">
        <div className="p-6 border-b border-slate-100">
          <h2 className="text-lg font-semibold text-dark flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary" />
            Predictions by User
          </h2>
        </div>
        <div className="p-6">
          {stats?.predictions_by_user && stats.predictions_by_user.length > 0 ? (
            <div className="space-y-3">
              {stats.predictions_by_user.map((item) => (
                <div key={item.username} className="flex items-center justify-between">
                  <span className="font-medium text-dark">{item.username}</span>
                  <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm font-medium">
                    {item.pred_count} predictions
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted text-center py-4">No predictions yet</p>
          )}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-2xl shadow-lg border border-slate-100 overflow-hidden">
        <div className="p-6 border-b border-slate-100">
          <h2 className="text-lg font-semibold text-dark flex items-center gap-2">
            <Clock className="w-5 h-5 text-primary" />
            Recent Activity
          </h2>
        </div>
        <div className="divide-y divide-slate-100">
          {stats?.recent_predictions?.slice(0, 5).map((pred) => (
            <div key={pred.id} className="p-4 hover:bg-slate-50 transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-dark truncate">{pred.text}</p>
                  <p className="text-xs text-muted mt-1">
                    by {pred.username || 'Anonymous'} • {new Date(pred.created_at).toLocaleString()}
                  </p>
                </div>
                <span
                  className={`ml-4 px-2 py-1 text-xs font-medium rounded-full ${
                    pred.prediction === 'depression'
                      ? 'bg-depression/10 text-depression'
                      : 'bg-normal/10 text-normal'
                  }`}
                >
                  {pred.prediction}
                </span>
              </div>
            </div>
          )) || (
            <p className="p-4 text-muted text-center">No recent activity</p>
          )}
        </div>
      </div>
    </div>
  );
}
