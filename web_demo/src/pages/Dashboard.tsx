import { Card, CardContent } from '@/components/ui/Card';
import { dashboardStats } from '@/data/mockData';
import { Database, Brain, Target, TrendingUp, Calendar, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTranslation } from 'react-i18next';
import { i18nKeys } from '../i18n/keys';

export default function Dashboard() {
  const { t } = useTranslation();

  const statCards = [
    {
      label: t(i18nKeys.dashboard.totalComments),
      value: dashboardStats.totalComments.toLocaleString(),
      icon: Database,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      label: t(i18nKeys.dashboard.currentModel),
      value: dashboardStats.currentModel,
      icon: Brain,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
      small: true,
    },
    {
      label: t(i18nKeys.dashboard.accuracy),
      value: `${dashboardStats.metrics.accuracy}%`,
      icon: Target,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
    },
    {
      label: t(i18nKeys.dashboard.macroF1),
      value: `${dashboardStats.metrics.macroF1}%`,
      icon: TrendingUp,
      color: 'text-violet-600',
      bgColor: 'bg-violet-50',
    },
    {
      label: t(i18nKeys.dashboard.weightedF1),
      value: `${dashboardStats.metrics.weightedF1}%`,
      icon: Activity,
      color: 'text-amber-600',
      bgColor: 'bg-amber-50',
    },
    {
      label: t(i18nKeys.dashboard.trainingDate),
      value: dashboardStats.trainingDate,
      icon: Calendar,
      color: 'text-slate-600',
      bgColor: 'bg-slate-100',
      small: true,
    },
  ];

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

      {/* Stats Grid */}
      <section className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map((stat, index) => (
          <Card
            key={stat.label}
            hover
            className={cn(
              'relative overflow-hidden',
              index === 0 && 'animate-breathe'
            )}
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <CardContent className="p-5">
              <div className={cn('flex items-center gap-3 mb-3', stat.small && 'flex-col items-start')}>
                <div className={cn('p-2.5 rounded-xl', stat.bgColor)}>
                  <stat.icon className={cn('w-5 h-5', stat.color)} />
                </div>
              </div>
              <p className={cn('font-mono font-bold text-dark', stat.small ? 'text-lg' : 'text-2xl')}>
                {stat.value}
              </p>
              <p className="text-sm text-muted mt-1">{stat.label}</p>
            </CardContent>
            {/* Breathing glow effect */}
            <div className={cn('absolute inset-0 rounded-2xl opacity-0', index === 0 && 'animate-pulse bg-gradient-to-r from-primary/5 to-transparent')} />
          </Card>
        ))}
      </section>

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
                  <span className={cn('px-4 py-2 rounded-full font-medium', component.color, component.border, 'border')}>
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
