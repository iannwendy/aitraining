import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { predict } from '@/services/api';
import { AlertTriangle, CheckCircle, Brain, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTranslation } from 'react-i18next';
import { i18nKeys } from '../i18n/keys';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { SkeletonPrediction } from '@/components/ui/Skeleton';
import { Button } from '@/components/ui/Button';
import { Upload } from 'lucide-react';

export default function Home() {
  const { t } = useTranslation();
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{
    prediction: 'depression' | 'normal';
    confidence: number;
    topic: string | undefined;
    riskLevel: 'low' | 'medium' | 'high';
    explanation?: string;
    modelName?: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handlePredict = async () => {
    if (!inputText.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const res = await predict(inputText);
      setResult({
        prediction: res.prediction,
        confidence: res.confidence,
        topic: res.topic,
        riskLevel: res.riskLevel,
        explanation: res.explanation,
        modelName: res.modelName,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Prediction failed');
    } finally {
      setIsLoading(false);
    }
  };

  const confidenceBars = [
    {
      label: t(i18nKeys.common.normal),
      value: result
        ? result.prediction === 'normal'
          ? result.confidence * 100
          : (1 - result.confidence) * 100
        : 0,
      color: 'bg-normal',
    },
    {
      label: t(i18nKeys.common.depression),
      value: result
        ? result.prediction === 'depression'
          ? result.confidence * 100
          : (1 - result.confidence) * 100
        : 0,
      color: 'bg-depression',
    },
  ];

  return (
    <ErrorBoundary>
      <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
        {/* Hero Section */}
        <section className="text-center space-y-4 py-8">
          <h1 className="font-display text-4xl sm:text-5xl font-bold text-dark">
            <span className="bg-gradient-to-r from-primary to-primary-light bg-clip-text text-transparent">
              {t(i18nKeys.home.title)}
            </span>
            <br />
            {t(i18nKeys.home.subtitle)}
          </h1>
          <p className="text-muted text-lg max-w-2xl mx-auto">
            {t(i18nKeys.home.heroDescription)}
          </p>
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
        {isLoading && (
          <SkeletonPrediction />
        )}

        {/* Input Section */}
        <Card>
          <CardContent className="p-8">
            <label className="block text-sm font-medium text-dark mb-3">
              {t(i18nKeys.prediction.inputLabel)}
            </label>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={t(i18nKeys.prediction.inputPlaceholder)}
              className="input-field min-h-[150px] resize-y font-body"
              disabled={isLoading}
            />
            <div className="flex justify-between items-center mt-4">
              <p className="text-sm text-muted">
                {inputText.length} {t(i18nKeys.common.characters)}
              </p>
              <Button
                onClick={handlePredict}
                isLoading={isLoading}
                disabled={!inputText.trim()}
                size="lg"
              >
                <Brain className="w-5 h-5" />
                {t(i18nKeys.button.analyze)}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results Section */}
        {result && (
          <div className="space-y-6 animate-slide-up">
            {/* Main Result Card */}
            <Card
              className={cn(
                'overflow-hidden',
                result.prediction === 'depression' ? 'ring-2 ring-depression/20' : 'ring-2 ring-normal/20',
              )}
            >
              <CardContent className="p-8">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-4">
                    {result.prediction === 'depression' ? (
                      <div className="p-4 rounded-2xl bg-depression/10">
                        <AlertTriangle className="w-10 h-10 text-depression" />
                      </div>
                    ) : (
                      <div className="p-4 rounded-2xl bg-normal/10">
                        <CheckCircle className="w-10 h-10 text-normal" />
                      </div>
                    )}
                    <div>
                      <h3
                        className={cn(
                          'font-display text-3xl font-bold',
                          result.prediction === 'depression' ? 'text-depression' : 'text-normal',
                        )}
                      >
                        {result.prediction === 'depression'
                          ? t(i18nKeys.common.depression)
                          : t(i18nKeys.common.normal)}
                      </h3>
                      <div className="flex items-center gap-2 mt-1">
                        <TrendingUp className="w-4 h-4 text-muted" />
                        <span className="text-muted">
                          {t(i18nKeys.common.confidence)}:{' '}
                          <span className="font-mono font-semibold text-dark">
                            {(result.confidence * 100).toFixed(1)}%
                          </span>
                        </span>
                      </div>
                      {result.modelName && (
                        <p className="text-xs text-muted mt-0.5">{result.modelName}</p>
                      )}
                    </div>
                  </div>

                  {/* Risk Badge */}
                  <div
                    className={cn(
                      'px-4 py-2 rounded-full font-semibold text-sm',
                      result.riskLevel === 'high' && 'bg-depression text-white',
                      result.riskLevel === 'medium' && 'bg-amber-100 text-amber-800',
                      result.riskLevel === 'low' && 'bg-normal text-white',
                    )}
                  >
                    {t(i18nKeys.common.risk)}:{' '}
                    {result.riskLevel === 'high'
                      ? t(i18nKeys.risk.high)
                      : result.riskLevel === 'medium'
                        ? t(i18nKeys.risk.medium)
                        : t(i18nKeys.risk.low)}
                  </div>
                </div>

                {/* Confidence Bars */}
                <div className="space-y-3">
                  {confidenceBars.map((bar) => (
                    <div key={bar.label}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-muted">{bar.label}</span>
                        <span className="font-mono font-medium">{(bar.value).toFixed(1)}%</span>
                      </div>
                      <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className={cn('h-full rounded-full transition-all duration-1000', bar.color)}
                          style={{ width: `${bar.value}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Topic & Explanation */}
            <div className="grid md:grid-cols-2 gap-6">
              {result.topic && (
                <Card hover>
                  <CardContent className="p-6">
                    <h4 className="text-sm font-medium text-muted mb-2">
                      {t(i18nKeys.prediction.detectedTopic)}
                    </h4>
                    <p className="font-display text-xl font-semibold text-primary">
                      {result.topic}
                    </p>
                  </CardContent>
                </Card>
              )}

              {result.explanation && (
                <Card hover>
                  <CardContent className="p-6">
                    <h4 className="text-sm font-medium text-muted mb-2">
                      {t(i18nKeys.prediction.explanation)}
                    </h4>
                    <p className="text-dark">{result.explanation}</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}

        {/* Batch Processing Card */}
        <Card hover className="group cursor-pointer" onClick={() => window.location.href = '/batch'}>
          <CardContent className="p-8">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-display text-xl font-semibold text-dark mb-2 group-hover:text-primary transition-colors">
                  {t(i18nKeys.home.batchProcessing)}
                </h3>
                <p className="text-muted">
                  {t(i18nKeys.home.uploadCsvDescription)}
                </p>
              </div>
              <div className="p-3 rounded-xl bg-accent/10 group-hover:bg-accent/20 transition-colors">
                <Upload className="w-6 h-6 text-accent" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </ErrorBoundary>
  );
}
