import { Card, CardContent } from '@/components/ui/Card';
import { topics } from '@/data/mockData';
import { Network, Tag, BarChart2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function Topics() {
  const topicColors = [
    'from-red-500 to-orange-500',
    'from-orange-500 to-amber-500',
    'from-amber-500 to-yellow-500',
    'from-purple-500 to-pink-500',
    'from-pink-500 to-rose-500',
    'from-slate-500 to-gray-500',
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <section className="text-center space-y-2">
        <h1 className="font-display text-3xl font-bold text-dark">
          Topic Analysis
        </h1>
        <p className="text-muted">
          BERTopic analysis revealing common themes in depression-related texts
        </p>
      </section>

      {/* Overview Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Topics', value: topics.length },
          { label: 'Top Topic', value: topics[0].name },
          { label: 'Most Frequent', value: `${topics[0].count.toLocaleString()} comments` },
          { label: 'Coverage', value: '100%' },
        ].map((stat) => (
          <Card key={stat.label} hover>
            <CardContent className="p-4 text-center">
              <p className="text-sm text-muted">{stat.label}</p>
              <p className="font-display text-xl font-bold text-primary mt-1">{stat.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Topics Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {topics.map((topic, index) => (
          <Card key={topic.id} hover className="overflow-hidden">
            {/* Topic Header with Gradient */}
            <div className={cn('h-2 bg-gradient-to-r', topicColors[index])} />

            <CardContent className="p-6">
              {/* Topic Name & Count */}
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-display text-lg font-semibold text-dark">
                    Topic {topic.id}: {topic.name}
                  </h3>
                  <p className="text-sm text-muted mt-1">
                    {topic.count.toLocaleString()} comments ({topic.percentage}%)
                  </p>
                </div>
                <div className={cn('p-2 rounded-xl bg-gradient-to-br', topicColors[index], 'opacity-80')}>
                  <Network className="w-5 h-5 text-white" />
                </div>
              </div>

              {/* Keywords */}
              <div className="mb-4">
                <div className="flex items-center gap-2 text-sm text-muted mb-2">
                  <Tag className="w-4 h-4" />
                  <span>Top Keywords</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {topic.keywords.map((keyword) => (
                    <span
                      key={keyword}
                      className={cn(
                        'px-3 py-1 rounded-full text-sm font-medium bg-gradient-to-r text-white',
                        topicColors[index]
                      )}
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>

              {/* Example Comments */}
              <div>
                <div className="flex items-center gap-2 text-sm text-muted mb-2">
                  <BarChart2 className="w-4 h-4" />
                  <span>Example Comments</span>
                </div>
                <div className="space-y-2">
                  {topic.examples.map((example, i) => (
                    <p key={i} className="text-sm text-slate-600 bg-slate-50 p-2 rounded-lg italic">
                      "{example}"
                    </p>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Distribution Chart Placeholder */}
      <Card>
        <CardContent className="p-6">
          <h3 className="font-display text-lg font-semibold text-dark mb-4">
            Topic Distribution
          </h3>
          <div className="space-y-3">
            {topics.map((topic, index) => (
              <div key={topic.id} className="flex items-center gap-4">
                <span className="w-32 text-sm font-medium text-dark truncate">
                  {topic.name}
                </span>
                <div className="flex-1 h-8 bg-slate-100 rounded-lg overflow-hidden">
                  <div
                    className={cn('h-full bg-gradient-to-r rounded-lg transition-all duration-1000', topicColors[index])}
                    style={{ width: `${topic.percentage}%` }}
                  />
                </div>
                <span className="w-16 text-sm text-muted text-right">
                  {topic.percentage}%
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
