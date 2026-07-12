import { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Upload, Download, FileText, AlertTriangle, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { batchPredict } from '@/services/api';
import { PredictionResult } from '@/types';
import { i18nKeys } from '../i18n/keys';

export default function BatchPrediction() {
  const { t } = useTranslation();
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState<PredictionResult[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
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
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
          {error}
        </div>
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
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.txt"
              onChange={handleFileChange}
              className="hidden"
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
                  {results.map((result, index) => (
                    <tr
                      key={index}
                      className="border-b border-slate-100 hover:bg-slate-50 transition-colors"
                    >
                      <td className="py-4 px-4 text-dark max-w-md truncate">
                        {result.text}
                      </td>
                      <td className="py-4 px-4">
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
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
