import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '@/components/ui/Card';
import type { ModelComparison } from '@/types';
import { getModelComparison } from '@/services/api';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  ScatterChart, Scatter,
} from 'recharts';
import { cn } from '@/lib/utils';
import { Trophy, TrendingUp, Beaker } from 'lucide-react';
import { i18nKeys } from '../i18n/keys';

export default function ModelComparison() {
  const { t } = useTranslation();
  const [models, setModels] = useState<ModelComparison[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getModelComparison();
      setModels(data.models);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load model comparison');
    } finally {
      setIsLoading(false);
    }
  };

  // Best in-domain model (highest in_domain_f1)
  const bestInDomain = models.length > 0
    ? models.reduce((best, m) => (m.in_domain_f1 > best.in_domain_f1 ? m : best), models[0])
    : null;

  // Best cross-domain model
  const bestCross = models.length > 0
    ? models.reduce((best, m) => (m.cross_domain_f1 > best.cross_domain_f1 ? m : best), models[0])
    : null;

  const getModelBadge = (model: ModelComparison) => {
    if (model.note === 'Best cross-domain') {
      return (
        <span className="ml-2 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 text-xs font-medium border border-amber-200">
          <TrendingUp className="w-3 h-3" />
          Best Cross-Domain
        </span>
      );
    }
    if (model.note === 'DAPT counter-experiment') {
      return (
        <span className="ml-2 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 text-xs font-medium border border-purple-200">
          <Beaker className="w-3 h-3" />
          DAPT
        </span>
      );
    }
    return null;
  };

  // Scatter data for in-domain vs cross-domain plot
  const scatterData = models.map((m) => ({
    name: m.name,
    in_domain: Math.round(m.in_domain_f1 * 100),
    cross_domain: Math.round(m.cross_domain_f1 * 100),
    isBestIn: m.name === bestInDomain?.name,
    isBestCross: m.name === bestCross?.name,
    type: m.model_type,
  }));

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <section className="text-center space-y-2">
        <h1 className="font-display text-3xl font-bold text-dark">
          {t(i18nKeys.compare.title)}
        </h1>
        <p className="text-muted">
          {t(i18nKeys.prediction.description)}
        </p>
      </section>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Best Models Highlights */}
      {!isLoading && models.length > 0 && (
        <div className="grid md:grid-cols-2 gap-6">
          {/* Best In-Domain */}
          {bestInDomain && (
            <Card className="bg-gradient-to-br from-emerald-50 via-white to-teal-50 border-2 border-emerald-200">
              <CardContent className="p-8">
                <div className="flex items-center gap-4 mb-4">
                  <div className="p-4 rounded-2xl bg-emerald-100">
                    <Trophy className="w-10 h-10 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-sm text-emerald-600 font-medium">🏆 Best In-Domain</p>
                    <h2 className="font-display text-2xl font-bold text-dark">
                      {bestInDomain.name}
                      {getModelBadge(bestInDomain)}
                    </h2>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4 mt-4">
                  <div className="text-center p-3 bg-white rounded-xl shadow-sm">
                    <p className="text-2xl font-display font-bold text-dark">
                      {(bestInDomain.in_domain_f1 * 100).toFixed(1)}%
                    </p>
                    <p className="text-xs text-muted">In-Domain F1</p>
                  </div>
                  <div className="text-center p-3 bg-white rounded-xl shadow-sm">
                    <p className="text-2xl font-display font-bold text-dark">
                      {(bestInDomain.cross_domain_f1 * 100).toFixed(1)}%
                    </p>
                    <p className="text-xs text-muted">Cross-Domain F1</p>
                  </div>
                  {bestInDomain.std_in && (
                    <div className="text-center p-3 bg-white rounded-xl shadow-sm">
                      <p className="text-2xl font-display font-bold text-dark">
                        ±{(bestInDomain.std_in * 100).toFixed(2)}%
                      </p>
                      <p className="text-xs text-muted">Std (3 seeds)</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Best Cross-Domain */}
          {bestCross && bestCross.name !== bestInDomain?.name && (
            <Card className="bg-gradient-to-br from-amber-50 via-white to-orange-50 border-2 border-amber-200">
              <CardContent className="p-8">
                <div className="flex items-center gap-4 mb-4">
                  <div className="p-4 rounded-2xl bg-amber-100">
                    <TrendingUp className="w-10 h-10 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-sm text-amber-600 font-medium">📈 Best Cross-Domain</p>
                    <h2 className="font-display text-2xl font-bold text-dark">
                      {bestCross.name}
                      {getModelBadge(bestCross)}
                    </h2>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4 mt-4">
                  <div className="text-center p-3 bg-white rounded-xl shadow-sm">
                    <p className="text-2xl font-display font-bold text-dark">
                      {(bestCross.in_domain_f1 * 100).toFixed(1)}%
                    </p>
                    <p className="text-xs text-muted">In-Domain F1</p>
                  </div>
                  <div className="text-center p-3 bg-white rounded-xl shadow-sm">
                    <p className="text-2xl font-display font-bold text-amber-600">
                      {(bestCross.cross_domain_f1 * 100).toFixed(1)}%
                    </p>
                    <p className="text-xs text-muted">Cross-Domain F1</p>
                  </div>
                  {bestCross.std_cross && (
                    <div className="text-center p-3 bg-white rounded-xl shadow-sm">
                      <p className="text-2xl font-display font-bold text-dark">
                        ±{(bestCross.std_cross * 100).toFixed(2)}%
                      </p>
                      <p className="text-xs text-muted">Std (3 seeds)</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Scatter Plot: In-Domain vs Cross-Domain */}
      {!isLoading && models.length > 0 && (
        <Card>
          <CardContent className="p-6">
            <h3 className="font-display text-lg font-semibold text-dark mb-2">
              Generalization Gap: In-Domain vs Cross-Domain (VSMEC)
            </h3>
            <p className="text-sm text-muted mb-6">
              Each point is a model. Best models maximize both axes. DAPT and augmentation variants highlighted.
            </p>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                  <XAxis
                    dataKey="in_domain"
                    name="In-Domain F1"
                    type="number"
                    domain={[0.3, 1]}
                    tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                    tick={{ fill: '#64748B', fontSize: 11 }}
                    label={{ value: 'In-Domain F1', position: 'insideBottom', offset: -5, fill: '#64748B' }}
                  />
                  <YAxis
                    dataKey="cross_domain"
                    name="Cross-Domain F1"
                    type="number"
                    domain={[0.2, 0.6]}
                    tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                    tick={{ fill: '#64748B', fontSize: 11 }}
                    label={{ value: 'Cross-Domain F1 (VSMEC)', angle: -90, position: 'insideLeft', fill: '#64748B' }}
                  />
                  <Tooltip
                    formatter={(value: number, name: string) => [`${(value / 100).toFixed(1)}%`, name]}
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e2e8f0',
                      borderRadius: '12px',
                    }}
                  />
                  <Scatter
                    data={scatterData}
                    fill="#0D9488"
                  >
                    {scatterData.map((entry, index) => (
                      <rect
                        key={index}
                        x={entry.in_domain * 100 - 5}
                        y={entry.cross_domain * 100 - 5}
                        width={10}
                        height={10}
                        fill={
                          entry.isBestCross
                            ? '#F59E0B'
                            : entry.name.includes('DAPT')
                            ? '#A855F7'
                            : entry.name.includes('aug')
                            ? '#EC4899'
                            : '#0D9488'
                        }
                        rx={2}
                      />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </div>
            {/* Legend */}
            <div className="flex flex-wrap gap-4 mt-4 justify-center">
              {[
                { color: '#0D9488', label: 'Standard models' },
                { color: '#A855F7', label: 'DAPT variant' },
                { color: '#EC4899', label: 'Augmented' },
                { color: '#F59E0B', label: 'Best cross-domain' },
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-sm" style={{ backgroundColor: item.color }} />
                  <span className="text-xs text-muted">{item.label}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Bar Chart: In-Domain F1 */}
      {!isLoading && models.length > 0 && (
        <Card>
          <CardContent className="p-6">
            <h3 className="font-display text-lg font-semibold text-dark mb-2">
              In-Domain F1 Comparison
            </h3>
            <p className="text-sm text-muted mb-6">
              F1-macro on held-out in-domain test set ({t(i18nKeys.statistics.accuracy)})
            </p>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={models}>
                  <XAxis
                    dataKey="name"
                    tick={{ fill: '#64748B', fontSize: 10 }}
                    axisLine={{ stroke: '#E2E8F0' }}
                    tickLine={false}
                    interval={0}
                    angle={-20}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis
                    domain={[0, 1]}
                    tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                    tick={{ fill: '#64748B', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    formatter={(value: number) => [`${(value * 100).toFixed(1)}%`, 'In-Domain F1']}
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e2e8f0',
                      borderRadius: '12px',
                    }}
                  />
                  <Bar
                    dataKey="in_domain_f1"
                    radius={[8, 8, 0, 0]}
                    fill="#0D9488"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Full Comparison Table */}
      {!isLoading && models.length > 0 && (
        <Card>
          <CardContent className="p-6">
            <h3 className="font-display text-lg font-semibold text-dark mb-6">
              {t(i18nKeys.compare.fullComparisonTable)}
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-4 px-4 text-sm font-semibold text-muted">Model</th>
                    <th className="text-right py-4 px-4 text-sm font-semibold text-muted">In-Domain F1</th>
                    <th className="text-right py-4 px-4 text-sm font-semibold text-muted">Cross-Domain F1</th>
                    <th className="text-right py-4 px-4 text-sm font-semibold text-muted">±In (std)</th>
                    <th className="text-right py-4 px-4 text-sm font-semibold text-muted">±Cross (std)</th>
                    <th className="text-left py-4 px-4 text-sm font-semibold text-muted">Type</th>
                  </tr>
                </thead>
                <tbody>
                  {models.map((model) => {
                    const isBestIn = model.name === bestInDomain?.name;
                    const isBestCross = model.name === bestCross?.name;
                    return (
                      <tr
                        key={model.name}
                        className={cn(
                          'border-b border-slate-100 transition-colors hover:bg-slate-50',
                          isBestIn && 'bg-emerald-50/50',
                        )}
                      >
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-2">
                            {isBestIn && <Trophy className="w-4 h-4 text-emerald-500 flex-shrink-0" />}
                            {isBestCross && !isBestIn && <TrendingUp className="w-4 h-4 text-amber-500 flex-shrink-0" />}
                            <span
                              className={cn(
                                'font-semibold',
                                isBestIn ? 'text-emerald-700' : 'text-dark',
                              )}
                            >
                              {model.name}
                            </span>
                            {getModelBadge(model)}
                          </div>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <span
                            className={cn(
                              'font-mono font-semibold',
                              isBestIn ? 'text-emerald-600' : 'text-dark',
                            )}
                          >
                            {(model.in_domain_f1 * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <span
                            className={cn(
                              'font-mono',
                              isBestCross ? 'text-amber-600 font-semibold' : 'text-dark',
                            )}
                          >
                            {(model.cross_domain_f1 * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-4 px-4 text-right text-muted font-mono text-sm">
                          {model.std_in != null ? `±${(model.std_in * 100).toFixed(2)}%` : '—'}
                        </td>
                        <td className="py-4 px-4 text-right text-muted font-mono text-sm">
                          {model.std_cross != null ? `±${(model.std_cross * 100).toFixed(2)}%` : '—'}
                        </td>
                        <td className="py-4 px-4">
                          <span
                            className={cn(
                              'px-2 py-1 rounded-full text-xs font-medium',
                              model.model_type === 'baseline' && 'bg-slate-100 text-slate-600',
                              model.model_type === 'bilstm' && 'bg-blue-100 text-blue-700',
                              model.model_type === 'phobert' && 'bg-orange-100 text-orange-700',
                              model.model_type === 'hybrid' && 'bg-teal-100 text-teal-700',
                              model.model_type === 'bertopic' && 'bg-purple-100 text-purple-700',
                            )}
                          >
                            {model.model_type}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Loading skeleton */}
      {isLoading && (
        <div className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {[0, 1].map((i) => (
              <Card key={i}>
                <CardContent className="p-8 animate-pulse">
                  <div className="h-20 bg-slate-100 rounded-xl mb-4" />
                  <div className="h-12 bg-slate-100 rounded-xl" />
                </CardContent>
              </Card>
            ))}
          </div>
          <Card>
            <CardContent className="p-6 animate-pulse">
              <div className="h-80 bg-slate-100 rounded-xl" />
            </CardContent>
          </Card>
        </div>
      )}

      {/* DAPT Counter-Experiment Note */}
      {!isLoading && models.some((m) => m.note === 'DAPT counter-experiment') && (
        <Card className="bg-purple-50 border-purple-200">
          <CardContent className="p-6">
            <h3 className="font-display text-lg font-semibold text-purple-800 mb-3 flex items-center gap-2">
              <Beaker className="w-5 h-5" />
              DAPT Counter-Experiment
            </h3>
            <p className="text-sm text-purple-700 leading-relaxed">
              <strong>Domain-Adaptive Pre-Training (DAPT)</strong> là continued MLM pretraining
              trên 119,649 comments YouTube. Trước Round 3, DAPT <em>giảm</em> F1 downstream
              (~3.5-4 điểm). Sau Round 3 (dataset sạch hơn), DAPT cho <em>+0.012 F1</em> in-domain.
              Cross-domain giảm nhẹ (-0.011). Hiệu ứng ngược chiều này được ghi nhận là phát hiện chính
              của nghiên cứu. Kết quả: <strong>in-domain F1 88.0%</strong> (tốt nhất toàn bộ).
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
