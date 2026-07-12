import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '@/components/ui/Card';
import { Topic } from '@/types';
import { getTopics } from '@/services/api';
import { Network, Tag, BarChart2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { i18nKeys } from '../i18n/keys';

export default function Topics() {
  const { t } = useTranslation();
  const [topics, setTopics] = useState<Topic[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const topicColors = [
    'from-red-500 to-orange-500',
    'from-orange-500 to-amber-500',
    'from-amber-500 to-yellow-500',
    'from-purple-500 to-pink-500',
    'from-pink-500 to-rose-500',
    'from-teal-500 to-cyan-500',
    'from-indigo-500 to-purple-500',
    'from-blue-500 to-indigo-500',
  ];

  useEffect(() => {
    loadTopics();
  }, []);

  const loadTopics = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getTopics(20);
      setTopics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load topics');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <section className="text-center space-y-2">
        <h1 className="font-display text-3xl font-bold text-dark">
          {t(i18nKeys.topics.title)}
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

      {/* Overview Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-4 animate-pulse">
                <div className="h-8 bg-slate-100 rounded mb-2" />
                <div className="h-4 bg-slate-100 rounded w-3/4" />
              </CardContent>
            </Card>
          ))
        ) : (
          <>
            <Card hover>
              <CardContent className="p-4 text-center">
                <p className="text-sm text-muted">{t(i18nKeys.topics.totalTopics)}</p>
                <p className="font-display text-xl font-bold text-primary mt-1">
                  {topics.length}
                </p>
              </CardContent>
            </Card>
            <Card hover>
              <CardContent className="p-4 text-center">
                <p className="text-sm text-muted">{t(i18nKeys.topics.topTopic)}</p>
                <p className="font-display text-xl font-bold text-primary mt-1">
                  {topics[0]?.name || '—'}
                </p>
              </CardContent>
            </Card>
            <Card hover>
              <CardContent className="p-4 text-center">
                <p className="text-sm text-muted">{t(i18nKeys.topics.mostFrequent)}</p>
                <p className="font-display text-xl font-bold text-primary mt-1">
                  {topics[0]?.count?.toLocaleString() || '—'}
                </p>
              </CardContent>
            </Card>
            <Card hover>
              <CardContent className="p-4 text-center">
                <p className="text-sm text-muted">{t(i18nKeys.topics.coverage)}</p>
                <p className="font-display text-xl font-bold text-primary mt-1">
                  {topics.length > 0
                    ? `${topics
                        .slice(0, 5)
                        .reduce((s, t) => s + t.percentage, 0)
                        .toFixed(1)}%`
                    : '—'}
                </p>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Topics Grid */}
      {isLoading ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6 animate-pulse">
                <div className="h-2 bg-slate-100 rounded mb-4" />
                <div className="h-6 bg-slate-100 rounded mb-2 w-3/4" />
                <div className="h-4 bg-slate-100 rounded mb-4 w-1/2" />
                <div className="flex gap-2">
                  <div className="h-6 bg-slate-100 rounded-full w-16" />
                  <div className="h-6 bg-slate-100 rounded-full w-20" />
                  <div className="h-6 bg-slate-100 rounded-full w-14" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {topics.map((topic, index) => (
            <Card key={topic.id} hover className="overflow-hidden">
              {/* Topic Header with Gradient */}
              <div className={cn('h-2 bg-gradient-to-r', topicColors[index % topicColors.length])} />

              <CardContent className="p-6">
                {/* Topic Name & Count */}
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-display text-lg font-semibold text-dark">
                      Topic {topic.id}
                    </h3>
                    <p className="font-medium text-primary text-sm truncate max-w-[200px]">
                      {topic.name}
                    </p>
                    <p className="text-sm text-muted mt-1">
                      {topic.count.toLocaleString()} comments ({topic.percentage}%)
                    </p>
                  </div>
                  <div
                    className={cn(
                      'p-2 rounded-xl bg-gradient-to-br opacity-80',
                      topicColors[index % topicColors.length],
                    )}
                  >
                    <Network className="w-5 h-5 text-white" />
                  </div>
                </div>

                {/* Keywords */}
                {topic.keywords.length > 0 && (
                  <div className="mb-4">
                    <div className="flex items-center gap-2 text-sm text-muted mb-2">
                      <Tag className="w-4 h-4" />
                      <span>{t(i18nKeys.topics.topKeywords)}</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {topic.keywords.map((keyword) => (
                        <span
                          key={keyword}
                          className={cn(
                            'px-3 py-1 rounded-full text-sm font-medium bg-gradient-to-r text-white',
                            topicColors[index % topicColors.length],
                          )}
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Examples */}
                {topic.examples.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 text-sm text-muted mb-2">
                      <BarChart2 className="w-4 h-4" />
                      <span>{t(i18nKeys.topics.examples)}</span>
                    </div>
                    <div className="space-y-2">
                      {topic.examples.slice(0, 2).map((example, i) => (
                        <p
                          key={i}
                          className="text-sm text-slate-600 bg-slate-50 p-2 rounded-lg italic"
                        >
                          "{example}"
                        </p>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Distribution Chart */}
      {!isLoading && topics.length > 0 && (
        <Card>
          <CardContent className="p-6">
            <h3 className="font-display text-lg font-semibold text-dark mb-4">
              {t(i18nKeys.topics.distribution)}
            </h3>
            <div className="space-y-3">
              {topics.slice(0, 10).map((topic, index) => (
                <div key={topic.id} className="flex items-center gap-4">
                  <span className="w-16 text-sm font-medium text-dark truncate">
                    #{topic.id}
                  </span>
                  <span className="w-40 text-sm text-muted truncate">{topic.name}</span>
                  <div className="flex-1 h-6 bg-slate-100 rounded-lg overflow-hidden">
                    <div
                      className={cn(
                        'h-full bg-gradient-to-r rounded-lg transition-all duration-1000',
                        topicColors[index % topicColors.length],
                      )}
                      style={{ width: `${Math.max(topic.percentage, 1)}%` }}
                    />
                  </div>
                  <span className="w-14 text-sm text-muted text-right">
                    {topic.percentage}%
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
