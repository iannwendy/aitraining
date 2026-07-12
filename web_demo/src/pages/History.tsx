import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Search, Trash2, AlertTriangle, CheckCircle, Clock, Filter } from 'lucide-react';
import { cn } from '@/lib/utils';
import { i18nKeys } from '../i18n/keys';
import { getHistory, deleteHistoryEntry } from '@/services/api';
import { HistoryEntry } from '@/types';

export default function History() {
  const { t } = useTranslation();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterPrediction, setFilterPrediction] = useState<'all' | 'depression' | 'normal'>('all');
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getHistory(50, 0);
      setHistory(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load history');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteHistoryEntry(id);
      setHistory(history.filter((item) => item.id !== id));
      setTotal((prev) => prev - 1);
    } catch {
      // Silently fail — item may have been already deleted
    }
  };

  const filteredHistory = history.filter((item) => {
    const matchesSearch = item.text.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter =
      filterPrediction === 'all' || item.prediction === filterPrediction;
    return matchesSearch && matchesFilter;
  });

  const formatTime = (dateStr: string) => {
    try {
      return new Intl.DateTimeFormat('vi-VN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }).format(new Date(dateStr));
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <section className="text-center space-y-2">
        <h1 className="font-display text-3xl font-bold text-dark">
          {t(i18nKeys.history.title)}
        </h1>
        <p className="text-muted">
          {t(i18nKeys.prediction.description)}
        </p>
      </section>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4 items-center">
            {/* Search */}
            <div className="flex-1 min-w-[200px] relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted" />
              <input
                type="text"
                placeholder={t(i18nKeys.history.searchPlaceholder)}
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
                  {filter === 'all'
                    ? t(i18nKeys.history.filterAll)
                    : filter === 'depression'
                      ? t(i18nKeys.history.filterDepression)
                      : t(i18nKeys.history.filterNormal)}
                </Button>
              ))}
            </div>

            {/* Stats */}
            <div className="text-sm text-muted">
              {filteredHistory.length}
              {total > 0 && ` / ${total}`}{' '}
              {t(i18nKeys.history.title).toLowerCase()}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* History List */}
      <div className="space-y-4">
        {isLoading ? (
          <Card>
            <CardContent className="p-12 text-center">
              <Clock className="w-12 h-12 mx-auto text-muted mb-4 animate-pulse" />
              <p className="text-muted">Loading…</p>
            </CardContent>
          </Card>
        ) : filteredHistory.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <Clock className="w-12 h-12 mx-auto text-muted mb-4" />
              <p className="text-muted">{t(i18nKeys.history.noResults)}</p>
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
                      <span
                        className={cn(
                          'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold',
                          item.prediction === 'depression'
                            ? 'bg-depression/10 text-depression'
                            : 'bg-normal/10 text-normal',
                        )}
                      >
                        {item.prediction === 'depression' ? (
                          <AlertTriangle className="w-4 h-4" />
                        ) : (
                          <CheckCircle className="w-4 h-4" />
                        )}
                        {item.prediction.charAt(0).toUpperCase() + item.prediction.slice(1)}
                      </span>
                      <span className="text-sm text-muted flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {formatTime(item.created_at)}
                      </span>
                      <span
                        className={cn(
                          'px-2 py-0.5 rounded text-xs font-medium',
                          item.risk_level === 'high' && 'bg-depression/10 text-depression',
                          item.risk_level === 'medium' && 'bg-amber-100 text-amber-800',
                          item.risk_level === 'low' && 'bg-normal/10 text-normal',
                        )}
                      >
                        {t(i18nKeys.risk[item.risk_level] || item.risk_level)}
                      </span>
                    </div>

                    {/* Text */}
                    <p className="text-dark text-lg mb-3">"{item.text}"</p>

                    {/* Details */}
                    <div className="flex flex-wrap gap-4 text-sm">
                      <div>
                        <span className="text-muted">{t(i18nKeys.common.confidence)}: </span>
                        <span className="font-mono font-semibold">
                          {(item.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                      {item.topic && (
                        <div>
                          <span className="text-muted">{t(i18nKeys.common.topic)}: </span>
                          <span className="font-medium text-primary">{item.topic}</span>
                        </div>
                      )}
                      {item.model_name && (
                        <div>
                          <span className="text-muted">Model: </span>
                          <span className="text-muted">{item.model_name}</span>
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
