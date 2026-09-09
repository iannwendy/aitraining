import { useState, useMemo } from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import {
  AlertCircle,
  Play,
  ExternalLink,
  ThumbsUp,
  Eye,
  MessageSquare,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Search,
  ChevronUp,
  ChevronDown,
  Calendar,
  Heart,
  Activity,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface VideoMetadata {
  video_id: string;
  title: string;
  channel: string;
  view_count: number;
  like_count: number;
  comment_count: number;
  thumbnail_url: string;
  published_at: string;
}

interface Comment {
  comment_id: string;
  text: string;
  author: string;
  like_count: number;
  published_at: string;
  prediction?: 'depression' | 'normal' | null;
  confidence?: number | null;
  risk_level?: 'low' | 'medium' | 'high' | null;
  prob_depression?: number | null;
}

interface AnalysisSummary {
  total_comments: number;
  analyzed_comments: number;
  depression_count: number;
  normal_count: number;
  depression_rate: number;
  avg_confidence: number;
  overall_risk: 'low' | 'medium' | 'high';
  topic_distribution: Record<string, number>;
  high_risk_comments: Array<{
    text: string;
    confidence: number;
    risk_level: string;
  }>;
}

interface YouTubeFetchResponse {
  metadata: VideoMetadata;
  comments: Comment[];
  total_comments: number;
  analysis_summary: AnalysisSummary;
}

type SortKey = 'risk' | 'date' | 'likes';
type SortDir = 'asc' | 'desc';
type FilterRisk = 'all' | 'high' | 'medium' | 'low';

export default function YouTubeAnalysis() {
  const [url, setUrl] = useState('');
  const [maxComments, setMaxComments] = useState(100);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<YouTubeFetchResponse | null>(null);

  // Filters & sort
  const [searchQuery, setSearchQuery] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('risk');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [filterRisk, setFilterRisk] = useState<FilterRisk>('all');

  const handleAnalyze = async () => {
    if (!url.trim()) return;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/youtube/fetch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: JSON.stringify({
          url: url.trim(),
          max_comments: maxComments,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(errorData.detail || 'Failed to fetch YouTube data');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze video');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading && url.trim()) {
      handleAnalyze();
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString('vi-VN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  const getRiskBadge = (risk?: string | null) => {
    if (!risk) return null;
    const config = {
      high: { label: 'Cao', className: 'bg-red-100 text-red-700 border-red-300', icon: AlertTriangle },
      medium: { label: 'Trung bình', className: 'bg-amber-100 text-amber-700 border-amber-300', icon: Activity },
      low: { label: 'Thấp', className: 'bg-green-100 text-green-700 border-green-300', icon: CheckCircle },
    } as const;
    const cfg = config[risk as keyof typeof config];
    if (!cfg) return null;
    const Icon = cfg.icon;
    return (
      <span className={cn('inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border', cfg.className)}>
        <Icon className="w-3 h-3" />
        {cfg.label}
      </span>
    );
  };

  const getRiskCardColor = (risk?: string | null) => {
    switch (risk) {
      case 'high':
        return 'border-l-4 border-l-red-500 bg-red-50/30';
      case 'medium':
        return 'border-l-4 border-l-amber-500 bg-amber-50/30';
      case 'low':
        return 'border-l-4 border-l-green-500';
      default:
        return 'border-l-4 border-l-slate-300';
    }
  };

  // Risk weight for sorting
  const riskWeight = (risk?: string | null) => {
    if (risk === 'high') return 3;
    if (risk === 'medium') return 2;
    if (risk === 'low') return 1;
    return 0;
  };

  // Filtered and sorted comments
  const filteredComments = useMemo(() => {
    if (!result) return [];

    let list = result.comments;

    // Filter by risk
    if (filterRisk !== 'all') {
      list = list.filter((c) => c.risk_level === filterRisk);
    }

    // Search by keyword
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (c) =>
          c.text.toLowerCase().includes(q) ||
          c.author.toLowerCase().includes(q)
      );
    }

    // Sort
    const sorted = [...list].sort((a, b) => {
      let cmp = 0;
      if (sortKey === 'risk') {
        cmp = riskWeight(a.risk_level) - riskWeight(b.risk_level);
        // Tie-break by prob_depression
        if (cmp === 0) {
          cmp = (b.prob_depression || 0) - (a.prob_depression || 0);
        }
      } else if (sortKey === 'date') {
        cmp = new Date(b.published_at).getTime() - new Date(a.published_at).getTime();
      } else if (sortKey === 'likes') {
        cmp = b.like_count - a.like_count;
      }
      return sortDir === 'asc' ? -cmp : cmp;
    });

    return sorted;
  }, [result, searchQuery, sortKey, sortDir, filterRisk]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const SortIcon = ({ active, dir }: { active: boolean; dir: SortDir }) => (
    <span className="ml-1 inline-flex flex-col">
      <ChevronUp className={cn('w-3 h-3 -mb-1', active && dir === 'asc' ? 'text-primary' : 'text-slate-300')} />
      <ChevronDown className={cn('w-3 h-3', active && dir === 'desc' ? 'text-primary' : 'text-slate-300')} />
    </span>
  );

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <section className="text-center space-y-2">
        <h1 className="font-display text-3xl font-bold text-dark">
          YouTube Video Analysis
        </h1>
        <p className="text-muted">
          Phân tích bình luận từ video YouTube để phát hiện các dấu hiệu trầm cảm
        </p>
      </section>

      {/* Input Section */}
      <Card>
        <CardContent className="p-8">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark mb-2">
                YouTube Video URL
              </label>
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="https://www.youtube.com/watch?v=... hoặc https://youtu.be/..."
                className="input-field"
                disabled={isLoading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-dark mb-2">
                Số lượng bình luận tối đa (1-500)
              </label>
              <input
                type="number"
                value={maxComments}
                onChange={(e) => setMaxComments(Math.min(500, Math.max(1, parseInt(e.target.value) || 100)))}
                min={1}
                max={500}
                className="input-field w-32"
                disabled={isLoading}
              />
              <p className="text-xs text-muted mt-1">
                Nhiều bình luận hơn cho kết quả chính xác hơn nhưng mất thời gian xử lý lâu hơn
              </p>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                <p className="text-red-700 text-sm flex-1">{error}</p>
              </div>
            )}

            <div className="flex justify-end">
              <Button
                onClick={handleAnalyze}
                isLoading={isLoading}
                disabled={!url.trim()}
                size="lg"
              >
                <Play className="w-5 h-5" />
                Phân tích
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Loading State */}
      {isLoading && (
        <Card>
          <CardContent className="p-8">
            <div className="flex flex-col items-center justify-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent mb-4" />
              <p className="text-muted">Đang tải bình luận và phân tích...</p>
              <p className="text-sm text-muted mt-2">Việc này có thể mất vài phút tùy thuộc vào số lượng bình luận</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results Section */}
      {result && !isLoading && (
        <div className="space-y-6 animate-slide-up">
          {/* Video Metadata */}
          <Card>
            <CardContent className="p-6">
              <div className="flex gap-6">
                {result.metadata.thumbnail_url && (
                  <img
                    src={result.metadata.thumbnail_url}
                    alt={result.metadata.title}
                    className="w-64 rounded-lg flex-shrink-0 hidden sm:block"
                  />
                )}
                <div className="flex-1 min-w-0">
                  <h2 className="font-display text-xl font-semibold text-dark mb-2">
                    {result.metadata.title}
                  </h2>
                  <p className="text-muted mb-4">{result.metadata.channel}</p>

                  <div className="flex flex-wrap gap-4 text-sm">
                    <div className="flex items-center gap-1 text-muted">
                      <Eye className="w-4 h-4" />
                      <span>{formatNumber(result.metadata.view_count)} lượt xem</span>
                    </div>
                    <div className="flex items-center gap-1 text-muted">
                      <ThumbsUp className="w-4 h-4" />
                      <span>{formatNumber(result.metadata.like_count)} likes</span>
                    </div>
                    <div className="flex items-center gap-1 text-muted">
                      <MessageSquare className="w-4 h-4" />
                      <span>{formatNumber(result.metadata.comment_count)} bình luận</span>
                    </div>
                  </div>

                  <a
                    href={`https://www.youtube.com/watch?v=${result.metadata.video_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-sm text-primary hover:underline mt-4"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Mở video trên YouTube
                  </a>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Analysis Summary */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Risk Assessment */}
            <Card className={cn(
              'border-2',
              result.analysis_summary.overall_risk === 'high' && 'border-red-300 bg-red-50',
              result.analysis_summary.overall_risk === 'medium' && 'border-amber-300 bg-amber-50',
              result.analysis_summary.overall_risk === 'low' && 'border-green-300 bg-green-50',
            )}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-dark">Đánh giá rủi ro</h3>
                  <span className={cn(
                    'px-3 py-1 rounded-full text-sm font-semibold border',
                    result.analysis_summary.overall_risk === 'high' && 'bg-red-100 text-red-800 border-red-200',
                    result.analysis_summary.overall_risk === 'medium' && 'bg-amber-100 text-amber-800 border-amber-200',
                    result.analysis_summary.overall_risk === 'low' && 'bg-green-100 text-green-800 border-green-200',
                  )}>
                    {result.analysis_summary.overall_risk === 'high' ? '⚠️ Cao' :
                     result.analysis_summary.overall_risk === 'medium' ? '⚡ Trung bình' : '✅ Thấp'}
                  </span>
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-muted">Tỷ lệ trầm cảm</span>
                    <span className="font-mono font-semibold">
                      {(result.analysis_summary.depression_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted">Bình luận đã phân tích</span>
                    <span className="font-mono">{result.analysis_summary.analyzed_comments}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted">Độ tin cậy trung bình</span>
                    <span className="font-mono">{(result.analysis_summary.avg_confidence * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Distribution */}
            <Card>
              <CardContent className="p-6">
                <h3 className="font-semibold text-dark mb-4">Phân bố dự đoán</h3>

                {/* Progress bars */}
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-muted flex items-center gap-1">
                        <AlertTriangle className="w-4 h-4 text-red-500" />
                        Trầm cảm
                      </span>
                      <span className="font-mono font-semibold text-red-600">
                        {result.analysis_summary.depression_count} ({(result.analysis_summary.depression_count / result.analysis_summary.analyzed_comments * 100).toFixed(1)}%)
                      </span>
                    </div>
                    <div className="h-4 bg-red-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-red-500 rounded-full transition-all duration-1000"
                        style={{ width: `${(result.analysis_summary.depression_count / result.analysis_summary.analyzed_comments) * 100}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-muted flex items-center gap-1">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        Bình thường
                      </span>
                      <span className="font-mono font-semibold text-green-600">
                        {result.analysis_summary.normal_count} ({(result.analysis_summary.normal_count / result.analysis_summary.analyzed_comments * 100).toFixed(1)}%)
                      </span>
                    </div>
                    <div className="h-4 bg-green-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-green-500 rounded-full transition-all duration-1000"
                        style={{ width: `${(result.analysis_summary.normal_count / result.analysis_summary.analyzed_comments) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>

                {result.analysis_summary.high_risk_comments.length > 0 && (
                  <div className="mt-4 p-3 bg-red-50 rounded-lg border border-red-200">
                    <div className="flex items-center gap-2 text-sm text-red-700">
                      <TrendingUp className="w-4 h-4" />
                      <span>
                        {result.analysis_summary.high_risk_comments.length} bình luận có nguy cơ cao được phát hiện
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Comments List */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-dark">
                  Bình luận ({filteredComments.length}/{result.comments.length})
                </h3>
              </div>

              {/* Controls: search, filter, sort */}
              <div className="flex flex-col md:flex-row gap-3 mb-4">
                {/* Search */}
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Tìm kiếm theo nội dung hoặc tác giả..."
                    className="input-field pl-10"
                  />
                </div>

                {/* Filter by risk */}
                <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
                  {(['all', 'high', 'medium', 'low'] as FilterRisk[]).map((risk) => (
                    <button
                      key={risk}
                      onClick={() => setFilterRisk(risk)}
                      className={cn(
                        'px-3 py-1.5 rounded-md text-xs font-semibold transition',
                        filterRisk === risk
                          ? 'bg-white shadow text-dark'
                          : 'text-slate-500 hover:text-dark'
                      )}
                    >
                      {risk === 'all' && 'Tất cả'}
                      {risk === 'high' && '⚠️ Cao'}
                      {risk === 'medium' && '⚡ TB'}
                      {risk === 'low' && '✅ Thấp'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Sort buttons */}
              <div className="flex items-center gap-2 mb-4 text-sm">
                <span className="text-muted">Sắp xếp:</span>
                <button
                  onClick={() => toggleSort('risk')}
                  className={cn(
                    'inline-flex items-center px-3 py-1.5 rounded-md border transition',
                    sortKey === 'risk'
                      ? 'bg-primary text-white border-primary'
                      : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
                  )}
                >
                  <Activity className="w-3.5 h-3.5 mr-1" />
                  Mức độ
                  <SortIcon active={sortKey === 'risk'} dir={sortDir} />
                </button>
                <button
                  onClick={() => toggleSort('date')}
                  className={cn(
                    'inline-flex items-center px-3 py-1.5 rounded-md border transition',
                    sortKey === 'date'
                      ? 'bg-primary text-white border-primary'
                      : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
                  )}
                >
                  <Calendar className="w-3.5 h-3.5 mr-1" />
                  Ngày
                  <SortIcon active={sortKey === 'date'} dir={sortDir} />
                </button>
                <button
                  onClick={() => toggleSort('likes')}
                  className={cn(
                    'inline-flex items-center px-3 py-1.5 rounded-md border transition',
                    sortKey === 'likes'
                      ? 'bg-primary text-white border-primary'
                      : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
                  )}
                >
                  <Heart className="w-3.5 h-3.5 mr-1" />
                  Likes
                  <SortIcon active={sortKey === 'likes'} dir={sortDir} />
                </button>
              </div>

              {/* Comments list - all comments, scrollable */}
              <div className="space-y-3 max-h-[800px] overflow-y-auto pr-2">
                {filteredComments.length === 0 ? (
                  <div className="text-center py-8 text-muted">
                    {searchQuery || filterRisk !== 'all'
                      ? 'Không tìm thấy bình luận phù hợp'
                      : 'Không có bình luận'}
                  </div>
                ) : (
                  filteredComments.map((comment) => (
                    <div
                      key={comment.comment_id}
                      className={cn(
                        'p-4 bg-slate-50 rounded-lg transition hover:bg-slate-100',
                        getRiskCardColor(comment.risk_level)
                      )}
                    >
                      <div className="flex items-start justify-between mb-2 gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap mb-1">
                            <span className="font-medium text-sm text-dark">{comment.author}</span>
                            {getRiskBadge(comment.risk_level)}
                            {comment.prediction === 'depression' && (
                              <span className="text-xs text-red-600 font-medium">
                                ⚠️ Trầm cảm
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-slate-700 whitespace-pre-wrap break-words">
                            {comment.text}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between gap-4 mt-3 text-xs text-muted">
                        <div className="flex items-center gap-3">
                          <span className="flex items-center gap-1">
                            <ThumbsUp className="w-3 h-3" />
                            {comment.like_count}
                          </span>
                          {comment.confidence !== null && comment.confidence !== undefined && (
                            <span className="flex items-center gap-1 font-mono">
                              Tin cậy: {(comment.confidence * 100).toFixed(0)}%
                            </span>
                          )}
                        </div>
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {formatDate(comment.published_at)}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
