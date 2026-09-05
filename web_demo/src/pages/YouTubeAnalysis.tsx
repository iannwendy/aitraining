import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { AlertCircle, Play, ExternalLink, ThumbsUp, Eye, MessageSquare, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react';
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

export default function YouTubeAnalysis() {
  const { t } = useTranslation();
  const [url, setUrl] = useState('');
  const [maxComments, setMaxComments] = useState(100);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<YouTubeFetchResponse | null>(null);
  const [showComments, setShowComments] = useState(false);

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

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      default:
        return 'bg-green-100 text-green-800 border-green-200';
    }
  };

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
                    getRiskColor(result.analysis_summary.overall_risk)
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

                {/* High risk comments count */}
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

          {/* High Risk Comments */}
          {result.analysis_summary.high_risk_comments.length > 0 && (
            <Card className="border-red-200 bg-red-50/50">
              <CardContent className="p-6">
                <h3 className="font-display text-lg font-semibold text-dark mb-4 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-500" />
                  Bình luận có nguy cơ cao
                </h3>

                <div className="space-y-3">
                  {result.analysis_summary.high_risk_comments.map((comment, index) => (
                    <div
                      key={index}
                      className="p-4 bg-white rounded-lg border border-red-200"
                    >
                      <p className="text-dark text-sm mb-2">{comment.text}</p>
                      <div className="flex items-center gap-4 text-xs text-muted">
                        <span>Mức độ tự tin: {(comment.confidence * 100).toFixed(0)}%</span>
                        <span className={cn(
                          'px-2 py-0.5 rounded-full text-xs font-medium',
                          comment.risk_level === 'high' && 'bg-red-100 text-red-700',
                          comment.risk_level === 'medium' && 'bg-amber-100 text-amber-700',
                        )}>
                          {comment.risk_level === 'high' ? 'Cao' : 'Trung bình'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Comments List */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-dark">
                  Bình luận ({result.comments.length})
                </h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowComments(!showComments)}
                >
                  {showComments ? 'Ẩn bình luận' : 'Hiển thị bình luận'}
                </Button>
              </div>

              {showComments && (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {result.comments.slice(0, 50).map((comment) => (
                    <div
                      key={comment.comment_id}
                      className="p-4 bg-slate-50 rounded-lg"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-sm text-dark">{comment.author}</span>
                        <span className="text-xs text-muted flex items-center gap-1">
                          <ThumbsUp className="w-3 h-3" />
                          {comment.like_count}
                        </span>
                      </div>
                      <p className="text-sm text-slate-600">{comment.text}</p>
                    </div>
                  ))}
                  {result.comments.length > 50 && (
                    <p className="text-center text-sm text-muted py-2">
                      Hiển thị 50/{result.comments.length} bình luận
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
