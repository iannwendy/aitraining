import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '@/components/ui/Card';
import { topics, wordCloudData, confusionMatrix, dashboardStats } from '@/data/mockData';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer
} from 'recharts';
import { AlertTriangle, CheckCircle } from 'lucide-react';
import { i18nKeys } from '../i18n/keys';

export default function Statistics() {
  const { t } = useTranslation();
  // Pie Chart Data
  const pieData = [
    { name: 'Depression', value: 35, color: '#EF4444' },
    { name: 'Normal', value: 65, color: '#22C55E' },
  ];

  // Bar Chart Data
  const barData = topics.map((t, idx) => ({
    name: t.name,
    count: t.count,
    fill: ['#EF4444', '#F97316', '#FBBF24', '#A855F7', '#EC4899', '#64748B'][idx % 6],
  }));

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <section className="text-center space-y-2">
        <h1 className="font-display text-3xl font-bold text-dark">
          {t(i18nKeys.statistics.title)}
        </h1>
        <p className="text-muted">
          {t(i18nKeys.prediction.description)}
        </p>
      </section>

      {/* Main Charts Row */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Pie Chart */}
        <Card>
          <CardContent className="p-6">
            <h3 className="font-display text-lg font-semibold text-dark mb-6">
              {t(i18nKeys.statistics.predictionDist)}
            </h3>
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
                    formatter={(value: number) => [`${value}%`, 'Percentage']}
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e2e8f0',
                      borderRadius: '12px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
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
                  <span className="text-sm text-muted">({item.value}%)</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Bar Chart */}
        <Card>
          <CardContent className="p-6">
            <h3 className="font-display text-lg font-semibold text-dark mb-6">
              {t(i18nKeys.statistics.topicDist)}
            </h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData} layout="vertical">
                  <XAxis type="number" hide />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={120}
                    tick={{ fill: '#64748B', fontSize: 12 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    formatter={(value: number) => [value.toLocaleString(), 'Comments']}
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e2e8f0',
                      borderRadius: '12px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                    }}
                  />
                  <Bar dataKey="count" radius={[0, 8, 8, 0]}>
                    {barData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Word Cloud & Confusion Matrix Row */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Word Cloud */}
        <Card>
          <CardContent className="p-6">
            <h3 className="font-display text-lg font-semibold text-dark mb-6">
              {t(i18nKeys.statistics.wordCloud)}
            </h3>
            <div className="min-h-[300px] flex flex-wrap items-center justify-center gap-4 p-4">
              {wordCloudData.map((word) => (
                <span
                  key={word.text}
                  className="font-semibold transition-transform hover:scale-110 cursor-default"
                  style={{
                    fontSize: `${Math.max(14, Math.min(36, word.value / 3))}px`,
                    color: word.color || '#64748B',
                    opacity: 0.7 + (word.value / 100) * 0.3,
                  }}
                >
                  {word.text}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Confusion Matrix */}
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
                {/* Header Row */}
                <div className="w-12" />
                <div className="w-20 py-2 text-center text-xs font-medium text-muted">{t(i18nKeys.common.normal)}</div>
                <div className="w-20 py-2 text-center text-xs font-medium text-muted">{t(i18nKeys.common.depression)}</div>
              </div>

              {/* Normal Row */}
              <div className="flex gap-1 items-center">
                <div className="w-12 py-3 text-center text-xs font-medium text-muted">{t(i18nKeys.common.normal)}</div>
                <div className="w-20 h-16 flex items-center justify-center bg-normal/20 rounded-lg border border-normal/30">
                  <span className="font-mono font-semibold text-normal">{confusionMatrix.trueNegatives}</span>
                </div>
                <div className="w-20 h-16 flex items-center justify-center bg-slate-100 rounded-lg">
                  <span className="font-mono text-slate-400">{confusionMatrix.falsePositives}</span>
                </div>
              </div>

              {/* Depression Row */}
              <div className="flex gap-1 items-center">
                <div className="w-12 py-3 text-center text-xs font-medium text-muted">{t(i18nKeys.common.depression)}</div>
                <div className="w-20 h-16 flex items-center justify-center bg-slate-100 rounded-lg">
                  <span className="font-mono text-slate-400">{confusionMatrix.falseNegatives}</span>
                </div>
                <div className="w-20 h-16 flex items-center justify-center bg-depression/20 rounded-lg border border-depression/30">
                  <span className="font-mono font-semibold text-depression">{confusionMatrix.truePositives}</span>
                </div>
              </div>

              {/* Legend */}
              <div className="mt-6 grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-normal" />
                  <span className="text-muted">{t(i18nKeys.statistics.trueNegatives)}: {confusionMatrix.trueNegatives}</span>
                </div>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-depression" />
                  <span className="text-muted">{t(i18nKeys.statistics.truePositives)}: {confusionMatrix.truePositives}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Model Metrics */}
      <Card>
        <CardContent className="p-6">
          <h3 className="font-display text-lg font-semibold text-dark mb-6">
            {t(i18nKeys.statistics.currentModelPerformance)}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {[
              { label: t(i18nKeys.statistics.accuracy), value: `${dashboardStats.metrics.accuracy}%` },
              { label: t(i18nKeys.statistics.macroF1), value: `${dashboardStats.metrics.macroF1}%` },
              { label: t(i18nKeys.statistics.weightedF1), value: `${dashboardStats.metrics.weightedF1}%` },
              { label: t(i18nKeys.statistics.precision), value: `${dashboardStats.metrics.precision}%` },
              { label: t(i18nKeys.statistics.recall), value: `${dashboardStats.metrics.recall}%` },
            ].map((metric) => (
              <div key={metric.label} className="text-center p-4 bg-slate-50 rounded-xl">
                <p className="text-3xl font-display font-bold gradient-text">{metric.value}</p>
                <p className="text-sm text-muted mt-1">{metric.label}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
