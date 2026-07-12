import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { DashboardStatsExt } from '@/types';
import { getDashboardStats, triggerRefresh } from '@/services/api';
import { Database, Brain, Target, TrendingUp, Calendar, Activity, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTranslation } from 'react-i18next';
import { i18nKeys } from '../i18n/keys';

export default function Dashboard() {
  const { t } = useTranslation();
  const [stats, setStats] = useState<DashboardStatsExt | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getDashboardStats();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stats');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await triggerRefresh();
      await loadStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Refresh failed');
    } finally {
      setIsRefreshing(false);
    }
  };

  const statCards = stats
    ? [
        {
          label: t(i18nKeys.dashboard.totalComments),
          value: stats.totalComments.toLocaleString(),
          subLabel: `${stats.goldLabels.toLocaleString()} human-labeled`,
          icon: Database,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
        },
        {
          label: t(i18nKeys.dashboard.currentModel),
          value: stats.currentModel,
          subLabel: `Round ${stats.round}`,
          icon: Brain,
          color: 'text-primary',
          bgColor: 'bg-primary/10',
          small: true,
        },
        {
          label: 'In-Domain F1',
          value: stats.metrics.macroF1 > 0 ? `${(stats.metrics.macroF1 * 100).toFixed(1)}%` : '—',
          subLabel: t(i18nKeys.dashboard.accuracy),
          icon: Target,
          color: 'text-emerald-600',
          bgColor: 'bg-emerald-50',
        },
        {
          label: t(i18nKeys.dashboard.macroF1),
          value: stats.metrics.macroF1 > 0 ? `${(stats.metrics.macroF1 * 100).toFixed(1)}%` : '—',
          subLabel: 'In-domain',
          icon: TrendingUp,
          color: 'text-violet-600',
          bgColor: 'bg-violet-50',
        },
        {
          label: 'Cross-Domain F1',
          value: '—',
          subLabel: stats.bestCrossDomain,
          icon: Activity,
          color: 'text-amber-600',
          bgColor: 'bg-amber-50',
        },
        {
          label: t(i18nKeys.dashboard.trainingDate),
          value: stats.trainingDate
            ? new Date(stats.trainingDate).toLocaleDateString('vi-VN')
            : '—',
          subLabel: `Round ${stats.round}`,
          icon: Calendar,
          color: 'text-slate-600',
          bgColor: 'bg-slate-100',
          small: true,
        },
      ]
    : [];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero Section */}
      <section className="text-center space-y-4 py-8">
        <h1 className="font-display text-4xl sm:text-5xl font-bold text-dark">
          <span className="bg-gradient-to-r from-primary to-primary-light bg-clip-text text-transparent">
            {t(i18nKeys.dashboard.title)}
          </span>
          <br />
          {t(i18nKeys.dashboard.subtitle)}
        </h1>
        <p className="text-muted text-lg max-w-2xl mx-auto">
          Advanced NLP system using PhoBERT + BERTopic for detecting signs of depression
          in Vietnamese social media texts
        </p>
      </section>

      {/* Refresh Banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Stats Grid */}
      <section className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => (
              <Card key={i}>
                <CardContent className="p-5 animate-pulse">
                  <div className="h-10 bg-slate-100 rounded mb-2" />
                  <div className="h-4 bg-slate-100 rounded w-3/4" />
                </CardContent>
              </Card>
            ))
          : statCards.map((stat, index) => (
              <Card
                key={stat.label}
                hover
                className={cn(
                  'relative overflow-hidden',
                  index === 0 && 'animate-breathe',
                )}
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <CardContent className="p-5">
                  <div
                    className={cn(
                      'flex items-center gap-3 mb-3',
                      stat.small && 'flex-col items-start',
                    )}
                  >
                    <div className={cn('p-2.5 rounded-xl', stat.bgColor)}>
                      <stat.icon className={cn('w-5 h-5', stat.color)} />
                    </div>
                  </div>
                  <p
                    className={cn(
                      'font-mono font-bold text-dark',
                      stat.small ? 'text-lg' : 'text-2xl',
                    )}
                  >
                    {stat.value}
                  </p>
                  {stat.subLabel && (
                    <p className="text-sm text-muted mt-1">{stat.subLabel}</p>
                  )}
                  <p className="text-xs text-muted mt-0.5">{stat.label}</p>
                </CardContent>
                <div
                  className={cn(
                    'absolute inset-0 rounded-2xl opacity-0',
                    index === 0 && 'animate-pulse bg-gradient-to-r from-primary/5 to-transparent',
                  )}
                />
              </Card>
            ))}
      </section>

      {/* Refresh Button */}
      <div className="flex justify-end">
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium',
            'bg-slate-100 hover:bg-slate-200 text-slate-600',
            'transition-colors disabled:opacity-50',
          )}
        >
          <RefreshCw className={cn('w-4 h-4', isRefreshing && 'animate-spin')} />
          {isRefreshing ? 'Refreshing…' : 'Refresh Data'}
        </button>
      </div>

      {/* Quick Actions */}
      <section className="grid md:grid-cols-2 gap-6">
        <Card hover className="group cursor-pointer" onClick={() => window.location.href = '/prediction'}>
          <CardContent className="p-8">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-display text-xl font-semibold text-dark mb-2 group-hover:text-primary transition-colors">
                  {t(i18nKeys.dashboard.quickAnalysis)}
                </h3>
                <p className="text-muted">
                  Enter a Vietnamese text to analyze for depression indicators
                </p>
              </div>
              <div className="p-3 rounded-xl bg-primary/10 group-hover:bg-primary/20 transition-colors">
                <Brain className="w-6 h-6 text-primary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card hover className="group cursor-pointer" onClick={() => window.location.href = '/batch'}>
          <CardContent className="p-8">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-display text-xl font-semibold text-dark mb-2 group-hover:text-primary transition-colors">
                  {t(i18nKeys.dashboard.batchProcessing)}
                </h3>
                <p className="text-muted">
                  Upload a CSV file to analyze multiple texts at once
                </p>
              </div>
              <div className="p-3 rounded-xl bg-accent/10 group-hover:bg-accent/20 transition-colors">
                <TrendingUp className="w-6 h-6 text-accent" />
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* System Architecture */}
      <section>
        <h2 className="font-display text-2xl font-bold text-dark mb-6">System Architecture</h2>
        <Card>
          <CardContent className="p-8">
            <div className="flex flex-wrap items-center justify-center gap-4 text-sm">
              {[
                { name: 'React Frontend', color: 'bg-cyan-100 text-cyan-800', border: 'border-cyan-200' },
                { name: 'FastAPI Backend', color: 'bg-green-100 text-green-800', border: 'border-green-200' },
                { name: 'PhoBERT Model', color: 'bg-orange-100 text-orange-800', border: 'border-orange-200' },
                { name: 'BERTopic Service', color: 'bg-purple-100 text-purple-800', border: 'border-purple-200' },
                { name: 'SQLite Database', color: 'bg-slate-100 text-slate-800', border: 'border-slate-200' },
              ].map((component, index) => (
                <div key={component.name} className="flex items-center gap-2">
                  <span
                    className={cn(
                      'px-4 py-2 rounded-full font-medium',
                      component.color,
                      component.border,
                      'border',
                    )}
                  >
                    {component.name}
                  </span>
                  {index < 4 && <span className="text-muted">→</span>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
