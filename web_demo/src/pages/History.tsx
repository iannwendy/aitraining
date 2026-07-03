import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { predictionHistory } from '@/data/mockData';
import { Search, Trash2, AlertTriangle, CheckCircle, Clock, Filter } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function History() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterPrediction, setFilterPrediction] = useState<'all' | 'depression' | 'normal'>('all');
  const [history, setHistory] = useState(predictionHistory);

  const filteredHistory = history.filter((item) => {
    const matchesSearch = item.text.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterPrediction === 'all' || item.prediction === filterPrediction;
    return matchesSearch && matchesFilter;
  });

  const handleDelete = (id: string) => {
    setHistory(history.filter(item => item.id !== id));
  };

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('vi-VN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <section className="text-center space-y-2">
        <h1 className="font-display text-3xl font-bold text-dark">
          Prediction History
        </h1>
        <p className="text-muted">
          View and manage your previous text analysis results
        </p>
      </section>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4 items-center">
            {/* Search */}
            <div className="flex-1 min-w-[200px] relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted" />
              <input
                type="text"
                placeholder="Search predictions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input-field pl-10"
              />
            </div>

            {/* Filter Buttons */}
            <div className="flex gap-2">
              {(['all', 'depression', 'normal'] as const).map((filter) => (
                <Button
                  key={filter}
                  variant={filterPrediction === filter ? 'primary' : 'secondary'}
                  size="sm"
                  onClick={() => setFilterPrediction(filter)}
                >
                  <Filter className="w-4 h-4" />
                  {filter.charAt(0).toUpperCase() + filter.slice(1)}
                </Button>
              ))}
            </div>

            {/* Stats */}
            <div className="text-sm text-muted">
              {filteredHistory.length} of {history.length} predictions
            </div>
          </div>
        </CardContent>
      </Card>

      {/* History List */}
      <div className="space-y-4">
        {filteredHistory.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <Clock className="w-12 h-12 mx-auto text-muted mb-4" />
              <p className="text-muted">No predictions found</p>
            </CardContent>
          </Card>
        ) : (
          filteredHistory.map((item) => (
            <Card key={item.id} hover className="group">
              <CardContent className="p-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    {/* Prediction Badge & Time */}
                    <div className="flex items-center gap-3 mb-3">
                      <span className={cn(
                        'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold',
                        item.prediction === 'depression'
                          ? 'bg-depression/10 text-depression'
                          : 'bg-normal/10 text-normal'
                      )}>
                        {item.prediction === 'depression' ? (
                          <AlertTriangle className="w-4 h-4" />
                        ) : (
                          <CheckCircle className="w-4 h-4" />
                        )}
                        {item.prediction.charAt(0).toUpperCase() + item.prediction.slice(1)}
                      </span>
                      <span className="text-sm text-muted flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {formatTime(item.timestamp)}
                      </span>
                      {item.riskLevel && (
                        <span className={cn(
                          'px-2 py-0.5 rounded text-xs font-medium',
                          item.riskLevel === 'high' && 'bg-depression/10 text-depression',
                          item.riskLevel === 'medium' && 'bg-amber-100 text-amber-800',
                          item.riskLevel === 'low' && 'bg-normal/10 text-normal',
                        )}>
                          {item.riskLevel} risk
                        </span>
                      )}
                    </div>

                    {/* Text */}
                    <p className="text-dark text-lg mb-3">"{item.text}"</p>

                    {/* Details */}
                    <div className="flex flex-wrap gap-4 text-sm">
                      <div>
                        <span className="text-muted">Confidence: </span>
                        <span className="font-mono font-semibold">{item.confidence}%</span>
                      </div>
                      {item.topic && (
                        <div>
                          <span className="text-muted">Topic: </span>
                          <span className="font-medium text-primary">{item.topic}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Delete Button */}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(item.id)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Trash2 className="w-4 h-4 text-slate-400 hover:text-depression" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
