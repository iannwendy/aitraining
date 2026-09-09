import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Upload, Download, FileText, AlertTriangle, CheckCircle, X, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';
import { batchPredict } from '@/services/api';
import { PredictionResult } from '@/types';
import { i18nKeys } from '../i18n/keys';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { SkeletonBatch } from '@/components/ui/Skeleton';

export default function BatchPrediction() {
  const { t } = useTranslation();
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState<PredictionResult[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedResult, setSelectedResult] = useState<PredictionResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Close modal on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSelectedResult(null);
    };
    if (selectedResult) {
      document.addEventListener('keydown', handleEscape);
      // Prevent body scroll
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [selectedResult]);

  const getRiskLevel = (result: PredictionResult): 'high' | 'medium' | 'low' => {
    if (result.prediction === 'depression') {
      if (result.confidence >= 0.9) return 'high';
      if (result.confidence >= 0.7) return 'medium';
      return 'low';
    }
    return 'low';
  };

  const getRiskBadge = (risk: 'high' | 'medium' | 'low') => {
    const config = {
      high: { label: '⚠️ Cao', className: 'bg-red-100 text-red-700 border-red-300' },
      medium: { label: '⚡ Trung bình', className: 'bg-amber-100 text-amber-700 border-amber-300' },
      low: { label: '✅ Thấp', className: 'bg-green-100 text-green-700 border-green-300' },
    } as const;
    return config[risk];
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setShowResults(false);
      setError(null);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (isProcessing) return;
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      setFile(droppedFile);
      setShowResults(false);
      setError(null);
    }
  };

  const handleProcess = async () => {
    if (!file) return;

    setIsProcessing(true);
    setError(null);

    try {
      // Read file content
      const text = await file.text();
      const lines = text
        .split('\n')
        .map((l) => l.trim())
        .filter((l) => l.length > 0);

      // Support both CSV (header: comment) and plain text (one line per comment)
      let comments: string[];
      if (file.name.endsWith('.csv')) {
        // Skip header row if first line looks like a header
        const firstLine = lines[0]?.toLowerCase() || '';
        const startIndex =
          firstLine.includes('comment') || firstLine.includes('text')
            ? 1
            : 0;
        comments = lines.slice(startIndex);
      } else {
        comments = lines;
      }

      if (comments.length === 0) {
        setError('No comments found in file');
        setIsProcessing(false);
        return;
      }

      if (comments.length > 500) {
        setError(`Too many comments (${comments.length}). Maximum is 500.`);
        setIsProcessing(false);
        return;
      }

      const response = await batchPredict(comments);
      setResults(response.results);
      setShowResults(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Processing failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownloadCSV = () => {
    const csvContent = [
      ['Comment', 'Prediction', 'Confidence', 'Topic'],
      ...results.map((r) => [
        `"${r.text.replace(/"/g, '""')}"`,
        r.prediction,
        (r.confidence * 100).toFixed(1),
        r.topic || '',
      ]),
    ]
      .map((row) => row.join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'batch_predictions.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <ErrorBoundary>
      <div className="max-w-5xl mx-auto space-y-8 animate-fade-in">
        {/* Header */}
        <section className="text-center space-y-2">
          <h1 className="font-display text-3xl font-bold text-dark">
            {t(i18nKeys.batch.title)}
          </h1>
          <p className="text-muted">{t(i18nKeys.prediction.description)}</p>
        </section>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
            <p className="text-red-700 text-sm flex-1">{error}</p>
            <Button variant="outline" size="sm" onClick={() => { setError(null); }}>
              Dismiss
            </Button>
          </div>
        )}

        {/* Loading State */}
        {isProcessing && (
          <SkeletonBatch />
        )}

        {/* Upload Section */}
        <Card>
          <CardContent className="p-8">
            <div
              className={cn(
                'border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 cursor-pointer',
                file
                  ? 'border-primary bg-primary/5'
                  : 'border-slate-300 hover:border-primary/50 hover:bg-slate-50',
              )}
              onClick={() => !isProcessing && fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.txt"
                onChange={handleFileChange}
                className="hidden"
                disabled={isProcessing}
              />

              {file ? (
                <div className="space-y-4">
                  <div className="w-16 h-16 mx-auto rounded-2xl bg-primary/10 flex items-center justify-center">
                    <FileText className="w-8 h-8 text-primary" />
                  </div>
                <div>
                  <p className="font-semibold text-dark">{file.name}</p>
                  <p className="text-sm text-muted">
                    {(file.size / 1024).toFixed(1)} {t(i18nKeys.batch.fileSize)}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                    setShowResults(false);
                  }}
                >
                  {t(i18nKeys.button.remove)}
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-slate-100 flex items-center justify-center">
                  <Upload className="w-8 h-8 text-muted" />
                </div>
                <div>
                  <p className="font-semibold text-dark">
                    {t(i18nKeys.batch.dropzone)}
                  </p>
                  <p className="text-sm text-muted mt-1">
                    {t(i18nKeys.batch.supportsFormat)}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Sample Format */}
          <div className="mt-6 p-4 bg-slate-50 rounded-xl">
            <p className="text-sm font-medium text-dark mb-2">
              {t(i18nKeys.batch.format)}:
            </p>
            <pre className="text-xs font-mono text-muted bg-white p-3 rounded-lg overflow-x-auto">
{`comment
Tôi rất cô đơn.
Video hay quá.
Áp lực học tập thật kinh khủng.`}
            </pre>
          </div>

          <div className="flex justify-end mt-6">
            <Button
              onClick={handleProcess}
              disabled={!file || isProcessing}
              isLoading={isProcessing}
              size="lg"
            >
              <Upload className="w-5 h-5" />
              {t(i18nKeys.button.process)}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results Section */}
      {showResults && results.length > 0 && (
        <Card className="animate-slide-up">
          <CardContent className="p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-display text-xl font-semibold text-dark">
                {t(i18nKeys.batch.resultsTitle)} ({results.length}{' '}
                {t(i18nKeys.batch.resultsCount)})
              </h3>
              <Button onClick={handleDownloadCSV} variant="outline">
                <Download className="w-4 h-4" />
                {t(i18nKeys.button.download)} CSV
              </Button>
            </div>

            {/* Summary */}
            <div className="flex gap-4 mb-6">
              <div className="flex items-center gap-2 text-sm">
                <div className="w-3 h-3 rounded-full bg-depression" />
                <span className="text-muted">
                  Depression: {results.filter((r) => r.prediction === 'depression').length}
                </span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <div className="w-3 h-3 rounded-full bg-normal" />
                <span className="text-muted">
                  Normal: {results.filter((r) => r.prediction === 'normal').length}
                </span>
              </div>
            </div>

            {/* Results Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted">
                      {t(i18nKeys.batch.comment)}
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted">
                      {t(i18nKeys.batch.prediction)}
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted">
                      {t(i18nKeys.batch.confidence)}
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted">
                      {t(i18nKeys.batch.topic)}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((result, index) => {
                    const risk = getRiskLevel(result);
                    const riskBadge = getRiskBadge(risk);
                    return (
                      <tr
                        key={index}
                        onClick={() => setSelectedResult(result)}
                        className={cn(
                          'border-b border-slate-100 transition-colors cursor-pointer',
                          'hover:bg-slate-50',
                          risk === 'high' && 'bg-red-50/40 hover:bg-red-50',
                          risk === 'medium' && 'bg-amber-50/30 hover:bg-amber-50'
                        )}
                      >
                        <td className="py-4 px-4 text-dark max-w-md">
                          <div className="line-clamp-2">{result.text}</div>
                          <span className="text-xs text-primary mt-1 inline-block">
                            Click để xem đầy đủ →
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex flex-col gap-1 items-start">
                            <span
                              className={cn(
                                'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium',
                                result.prediction === 'depression'
                                  ? 'bg-depression/10 text-depression'
                                  : 'bg-normal/10 text-normal',
                              )}
                            >
                              {result.prediction === 'depression' ? (
                                <AlertTriangle className="w-4 h-4" />
                              ) : (
                                <CheckCircle className="w-4 h-4" />
                              )}
                              {result.prediction.charAt(0).toUpperCase() +
                                result.prediction.slice(1)}
                            </span>
                            <span
                              className={cn(
                                'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border',
                                riskBadge.className
                              )}
                            >
                              <Activity className="w-3 h-3" />
                              {riskBadge.label}
                            </span>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-2">
                            <div className="w-20 h-2 bg-slate-100 rounded-full overflow-hidden">
                              <div
                                className={cn(
                                  'h-full rounded-full',
                                  result.prediction === 'depression'
                                    ? 'bg-depression'
                                    : 'bg-normal',
                                )}
                                style={{ width: `${result.confidence * 100}%` }}
                              />
                            </div>
                            <span className="font-mono text-sm text-muted">
                              {(result.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                        </td>
                        <td className="py-4 px-4 text-sm text-muted">
                          {result.topic || '—'}
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

      {/* Full Comment Modal */}
      {selectedResult && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 animate-fade-in"
          onClick={() => setSelectedResult(null)}
        >
          <div
            className={cn(
              'bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden animate-slide-up',
              getRiskLevel(selectedResult) === 'high' && 'border-t-4 border-red-500',
              getRiskLevel(selectedResult) === 'medium' && 'border-t-4 border-amber-500',
              getRiskLevel(selectedResult) === 'low' && 'border-t-4 border-green-500',
            )}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-slate-200">
              <div className="flex items-center gap-3">
                <h3 className="font-display text-lg font-semibold text-dark">
                  Chi tiết bình luận
                </h3>
                {(() => {
                  const risk = getRiskLevel(selectedResult);
                  const badge = getRiskBadge(risk);
                  return (
                    <span
                      className={cn(
                        'inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold border',
                        badge.className
                      )}
                    >
                      <Activity className="w-3 h-3" />
                      Mức độ: {badge.label}
                    </span>
                  );
                })()}
              </div>
              <button
                onClick={() => setSelectedResult(null)}
                className="p-2 rounded-lg hover:bg-slate-100 transition"
                aria-label="Đóng"
              >
                <X className="w-5 h-5 text-slate-500" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
              {/* Full text */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-muted mb-2">
                  Nội dung đầy đủ
                </label>
                <div
                  className={cn(
                    'p-4 rounded-xl border-2 text-dark leading-relaxed whitespace-pre-wrap break-words',
                    getRiskLevel(selectedResult) === 'high' && 'bg-red-50 border-red-200',
                    getRiskLevel(selectedResult) === 'medium' && 'bg-amber-50 border-amber-200',
                    getRiskLevel(selectedResult) === 'low' && 'bg-green-50 border-green-200',
                  )}
                >
                  {selectedResult.text}
                </div>
                <div className="flex items-center gap-4 mt-2 text-xs text-muted">
                  <span>{selectedResult.text.length} ký tự</span>
                  <span>{selectedResult.text.split(/\s+/).filter(Boolean).length} từ</span>
                </div>
              </div>

              {/* Prediction details */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="p-4 bg-slate-50 rounded-xl">
                  <p className="text-xs text-muted uppercase mb-1">Dự đoán</p>
                  <p
                    className={cn(
                      'font-semibold text-lg',
                      selectedResult.prediction === 'depression' ? 'text-red-600' : 'text-green-600'
                    )}
                  >
                    {selectedResult.prediction === 'depression' ? '⚠️ Trầm cảm' : '✅ Bình thường'}
                  </p>
                </div>
                <div className="p-4 bg-slate-50 rounded-xl">
                  <p className="text-xs text-muted uppercase mb-1">Độ tin cậy</p>
                  <p className="font-semibold text-lg font-mono">
                    {(selectedResult.confidence * 100).toFixed(1)}%
                  </p>
                </div>
              </div>

              {/* Confidence bar */}
              <div className="mb-6">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-muted">Mức độ tự tin của mô hình</span>
                  <span className="font-mono">{(selectedResult.confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={cn(
                      'h-full rounded-full transition-all duration-700',
                      selectedResult.prediction === 'depression' ? 'bg-red-500' : 'bg-green-500'
                    )}
                    style={{ width: `${selectedResult.confidence * 100}%` }}
                  />
                </div>
              </div>

              {/* Topic */}
              {selectedResult.topic && (
                <div className="p-4 bg-primary/5 border border-primary/20 rounded-xl">
                  <p className="text-xs text-muted uppercase mb-1">Chủ đề</p>
                  <p className="font-medium text-dark">{selectedResult.topic}</p>
                </div>
              )}

              {/* Explanation if available */}
              {selectedResult.explanation && (
                <div className="mt-4 p-4 bg-slate-50 rounded-xl">
                  <p className="text-xs text-muted uppercase mb-1">Giải thích</p>
                  <p className="text-sm text-dark">{selectedResult.explanation}</p>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex justify-end gap-3 p-4 border-t border-slate-200 bg-slate-50">
              <Button variant="outline" onClick={() => setSelectedResult(null)}>
                Đóng
              </Button>
            </div>
          </div>
        </div>
      )}
      </div>
    </ErrorBoundary>
  );
}
