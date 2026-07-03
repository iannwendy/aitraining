import { Card, CardContent } from '@/components/ui/Card';
import { modelComparisons } from '@/data/mockData';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import { cn } from '@/lib/utils';
import { Trophy, TrendingUp } from 'lucide-react';

const metrics = ['accuracy', 'macroF1', 'weightedF1', 'precision', 'recall'] as const;
const metricLabels = {
  accuracy: 'Accuracy',
  macroF1: 'Macro F1',
  weightedF1: 'Weighted F1',
  precision: 'Precision',
  recall: 'Recall',
};

export default function ModelComparison() {
  const bestModel = modelComparisons[modelComparisons.length - 1];

  // Prepare radar data
  const radarData = metrics.map((metric) => ({
    metric: metricLabels[metric],
    value: Math.round((bestModel[metric] + 10) * 10) / 10,
    fullMark: 100,
  }));

  // Prepare bar data for each metric
  const barColors = ['#94A3B8', '#64748B', '#0D9488', '#F97316'];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <section className="text-center space-y-2">
        <h1 className="font-display text-3xl font-bold text-dark">
          Model Comparison
        </h1>
        <p className="text-muted">
          Compare performance across different deep learning architectures
        </p>
      </section>

      {/* Best Model Highlight */}
      <Card className="bg-gradient-to-br from-primary/5 via-white to-accent/5 border-2 border-primary/20">
        <CardContent className="p-8">
          <div className="flex items-center gap-4 mb-4">
            <div className="p-4 rounded-2xl bg-primary/10">
              <Trophy className="w-10 h-10 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted">Best Performing Model</p>
              <h2 className="font-display text-3xl font-bold gradient-text">
                {bestModel.name}
              </h2>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-6">
            {metrics.map((metric) => (
              <div key={metric} className="text-center p-4 bg-white rounded-xl shadow-sm">
                <p className="text-3xl font-display font-bold text-dark">
                  {bestModel[metric]}%
                </p>
                <p className="text-sm text-muted mt-1">{metricLabels[metric]}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Charts Row */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Radar Chart - Best Model */}
        <Card>
          <CardContent className="p-6">
            <h3 className="font-display text-lg font-semibold text-dark mb-2">
              {bestModel.name}
            </h3>
            <p className="text-sm text-muted mb-6">Performance Radar</p>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#E2E8F0" />
                  <PolarAngleAxis
                    dataKey="metric"
                    tick={{ fill: '#64748B', fontSize: 12 }}
                  />
                  <PolarRadiusAxis
                    angle={30}
                    domain={[0, 100]}
                    tick={{ fill: '#64748B', fontSize: 10 }}
                  />
                  <Radar
                    name={bestModel.name}
                    dataKey="value"
                    stroke="#0D9488"
                    fill="#0D9488"
                    fillOpacity={0.3}
                  />
                  <Tooltip
                    formatter={(value: number) => [`${value}%`, 'Score']}
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e2e8f0',
                      borderRadius: '12px',
                    }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Bar Chart - All Models */}
        <Card>
          <CardContent className="p-6">
            <h3 className="font-display text-lg font-semibold text-dark mb-2">
              Accuracy Comparison
            </h3>
            <p className="text-sm text-muted mb-6">Across All Models</p>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={modelComparisons}>
                  <XAxis
                    dataKey="name"
                    tick={{ fill: '#64748B', fontSize: 11 }}
                    axisLine={{ stroke: '#E2E8F0' }}
                    tickLine={false}
                  />
                  <YAxis
                    domain={[70, 100]}
                    tick={{ fill: '#64748B', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    formatter={(value: number, name: string) => [
                      `${value}%`,
                      metricLabels[name as keyof typeof metricLabels] || name
                    ]}
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e2e8f0',
                      borderRadius: '12px',
                    }}
                  />
                  <Bar dataKey="accuracy" radius={[8, 8, 0, 0]}>
                    {modelComparisons.map((_, index) => (
                      <rect key={`bar-${index}`} fill={barColors[index]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Model Comparison Table */}
      <Card>
        <CardContent className="p-6">
          <h3 className="font-display text-lg font-semibold text-dark mb-6">
            Full Comparison Table
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-4 px-4 text-sm font-semibold text-muted">Model</th>
                  {metrics.map((metric) => (
                    <th key={metric} className="text-right py-4 px-4 text-sm font-semibold text-muted">
                      {metricLabels[metric]}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {modelComparisons.map((model, index) => (
                  <tr
                    key={model.name}
                    className={cn(
                      'border-b border-slate-100 transition-colors hover:bg-slate-50',
                      index === modelComparisons.length - 1 && 'bg-primary/5'
                    )}
                  >
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-3">
                        {index === modelComparisons.length - 1 && (
                          <Trophy className="w-5 h-5 text-primary" />
                        )}
                        <span className={cn(
                          'font-semibold',
                          index === modelComparisons.length - 1 ? 'text-primary' : 'text-dark'
                        )}>
                          {model.name}
                        </span>
                      </div>
                    </td>
                    {metrics.map((metric) => (
                      <td key={metric} className="text-right py-4 px-4">
                        <span className="font-mono font-semibold">
                          {model[metric]}%
                        </span>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Improvement Stats */}
      <div className="grid md:grid-cols-3 gap-6">
        <Card hover className="bg-gradient-to-br from-emerald-50 to-white">
          <CardContent className="p-6 text-center">
            <TrendingUp className="w-8 h-8 mx-auto text-emerald-600 mb-2" />
            <p className="text-4xl font-display font-bold text-emerald-600">
              +12.2%
            </p>
            <p className="text-sm text-muted mt-1">
              Improvement over TF-IDF+SVM
            </p>
          </CardContent>
        </Card>

        <Card hover className="bg-gradient-to-br from-blue-50 to-white">
          <CardContent className="p-6 text-center">
            <TrendingUp className="w-8 h-8 mx-auto text-blue-600 mb-2" />
            <p className="text-4xl font-display font-bold text-blue-600">
              +7.2%
            </p>
            <p className="text-sm text-muted mt-1">
              Improvement over BiLSTM
            </p>
          </CardContent>
        </Card>

        <Card hover className="bg-gradient-to-br from-purple-50 to-white">
          <CardContent className="p-6 text-center">
            <TrendingUp className="w-8 h-8 mx-auto text-purple-600 mb-2" />
            <p className="text-4xl font-display font-bold text-purple-600">
              +2.2%
            </p>
            <p className="text-sm text-muted mt-1">
              Improvement over PhoBERT
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
