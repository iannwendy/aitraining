import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '@/components/ui/Card';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { AlertTriangle, CheckCircle } from 'lucide-react';
import { i18nKeys } from '../i18n/keys';
import { getStatistics } from '@/services/api';
import { StatisticsResponse } from '@/types';

export default function Statistics() {
  const { t } = useTranslation();
  const [stats, setStats] = useState<StatisticsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getStatistics();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load statistics');
    } finally {
      setIsLoading(false);
    }
  };

  const pieData = stats
    ? [
        {
          name: 'Depression',
          value: stats.class_distribution.depression,
          color: '#EF4444',
        },
        {
          name: 'Normal',
          value: stats.class_distribution.normal,
          color: '#22C55E',
        },
      ]
    : [];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <section className="text-center space-y-2">
        <h1 className="font-display text-3xl font-bold text-dark">
          {t(i18nKeys.statistics.title)}
        </h1>
        <p className="text-muted">{t(i18nKeys.prediction.description)}</p>
      </section>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Main Charts Row */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Pie Chart — Class Distribution */}
        <Card>
          <CardContent className="p-6">
            <h3 className="font-display text-lg font-semibold text-dark mb-6">
              {t(i18nKeys.statistics.predictionDist)}
            </h3>
            {isLoading ? (
              <div className="h-80 animate-pulse bg-slate-100 rounded-xl" />
            ) : pieData.length > 0 ? (
              <>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(value: number, name: string) => [
                          `${value.toLocaleString()} (${((value / (pieData[0].value + pieData[1].value)) * 100).toFixed(1)}%)`,
                          name,
                        ]}
                        contentStyle={{
                          backgroundColor: 'white',
                          border: '1px solid #e2e8f0',
                          borderRadius: '12px',
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                {/* Legend */}
                <div className="flex justify-center gap-8 mt-4">
                  {pieData.map((item) => (
                    <div key={item.name} className="flex items-center gap-2">
                      <div
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-sm font-medium text-dark">{item.name}</span>
                      <span className="text-sm text-muted">
                        ({item.value.toLocaleString()})
                      </span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="text-muted text-center py-8">No data available</p>
            )}
          </CardContent>
        </Card>

        {/* Bar Chart — Dataset Breakdown */}
        <Card>
          <CardContent className="p-6">
            <h3 className="font-display text-lg font-semibold text-dark mb-6">
              {t(i18nKeys.statistics.topicDist)}
            </h3>
            {isLoading ? (
              <div className="h-80 animate-pulse bg-slate-100 rounded-xl" />
            ) : stats ? (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={[
                      {
                        name: 'Gold-labeled',
                        count: stats.dataset_breakdown.gold,
                        fill: '#0D9488',
                      },
                      {
                        name: 'Pseudo-labeled',
                        count: stats.dataset_breakdown.pseudo,
                        fill: '#94A3B8',
                      },
                    ]}
                  >
                    <XAxis dataKey="name" tick={{ fill: '#64748B', fontSize: 12 }} />
                    <YAxis tick={{ fill: '#64748B', fontSize: 11 }} />
                    <Tooltip
                      formatter={(value: number) => [value.toLocaleString(), 'Samples']}
                      contentStyle={{
                        backgroundColor: 'white',
                        border: '1px solid #e2e8f0',
                        borderRadius: '12px',
                      }}
                    />
                    <Bar dataKey="count" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-muted text-center py-8">No data available</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Confusion Matrix */}
      {stats && (
        <Card>
          <CardContent className="p-6">
            <h3 className="font-display text-lg font-semibold text-dark mb-6">
              {t(i18nKeys.statistics.confusionMatrix)}
            </h3>
            <div className="flex flex-col items-center">
              <div className="text-center text-sm text-muted mb-2">
                <span className="inline-block w-24">{t(i18nKeys.statistics.actualPredicted)}</span>
              </div>
              <div className="flex gap-1">
                <div className="w-12" />
                <div className="w-20 py-2 text-center text-xs font-medium text-muted">
                  {t(i18nKeys.common.normal)}
                </div>
                <div className="w-20 py-2 text-center text-xs font-medium text-muted">
                  {t(i18nKeys.common.depression)}
                </div>
              </div>

              {/* Normal Row */}
              <div className="flex gap-1 items-center">
                <div className="w-12 py-3 text-center text-xs font-medium text-muted">
                  {t(i18nKeys.common.normal)}
                </div>
                <div className="w-20 h-16 flex items-center justify-center bg-normal/20 rounded-lg border border-normal/30">
                  <span className="font-mono font-semibold text-normal">
                    {stats.confusion_matrix[0]?.[0] ?? 0}
                  </span>
                </div>
                <div className="w-20 h-16 flex items-center justify-center bg-slate-100 rounded-lg">
                  <span className="font-mono text-slate-400">
                    {stats.confusion_matrix[0]?.[1] ?? 0}
                  </span>
                </div>
              </div>

              {/* Depression Row */}
              <div className="flex gap-1 items-center">
                <div className="w-12 py-3 text-center text-xs font-medium text-muted">
                  {t(i18nKeys.common.depression)}
                </div>
                <div className="w-20 h-16 flex items-center justify-center bg-slate-100 rounded-lg">
                  <span className="font-mono text-slate-400">
                    {stats.confusion_matrix[1]?.[0] ?? 0}
                  </span>
                </div>
                <div className="w-20 h-16 flex items-center justify-center bg-depression/20 rounded-lg border border-depression/30">
                  <span className="font-mono font-semibold text-depression">
                    {stats.confusion_matrix[1]?.[1] ?? 0}
                  </span>
                </div>
              </div>

              {/* Legend */}
              <div className="mt-6 grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-normal" />
                  <span className="text-muted">
                    {t(i18nKeys.statistics.trueNegatives)}: {stats.confusion_matrix[0]?.[0] ?? 0}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-depression" />
                  <span className="text-muted">
                    {t(i18nKeys.statistics.truePositives)}: {stats.confusion_matrix[1]?.[1] ?? 0}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Prediction Stats */}
      {stats && (
        <Card>
          <CardContent className="p-6">
            <h3 className="font-display text-lg font-semibold text-dark mb-6">
              Prediction Statistics
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                {
                  label: 'Total Predictions',
                  value: stats.prediction_stats.total,
                },
                {
                  label: 'Depression Rate',
                  value:
                    stats.prediction_stats.total > 0
                      ? `${(
                          (stats.prediction_stats.depression_count /
                            stats.prediction_stats.total) *
                          100
                        ).toFixed(1)}%`
                      : '—',
                },
                {
                  label: 'Avg Confidence',
                  value:
                    stats.prediction_stats.avg_confidence > 0
                      ? `${(stats.prediction_stats.avg_confidence * 100).toFixed(1)}%`
                      : '—',
                },
                {
                  label: 'Unique Topics',
                  value: stats.prediction_stats.unique_topics,
                },
              ].map((metric) => (
                <div
                  key={metric.label}
                  className="text-center p-4 bg-slate-50 rounded-xl"
                >
                  <p className="text-2xl font-display font-bold text-dark">
                    {metric.value}
                  </p>
                  <p className="text-sm text-muted mt-1">{metric.label}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
