import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { AlertTriangle, CheckCircle, Brain, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { topics } from '@/data/mockData';

export default function Prediction() {
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{
    prediction: 'depression' | 'normal';
    confidence: number;
    topic: string;
    riskLevel: 'low' | 'medium' | 'high';
    highlightedText?: string;
    explanation?: string;
  } | null>(null);

  const handlePredict = async () => {
    if (!inputText.trim()) return;

    setIsLoading(true);

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));

    // Mock result based on input
    const hasDepressionIndicators = inputText.includes('cô đơn') ||
      inputText.includes('mệt mỏi') ||
      inputText.includes('áp lực') ||
      inputText.includes('vô nghĩa') ||
      inputText.includes('buồn') ||
      inputText.includes('không muốn');

    const randomTopic = topics[Math.floor(Math.random() * topics.length)];

    setResult({
      prediction: hasDepressionIndicators ? 'depression' : 'normal',
      confidence: hasDepressionIndicators ? 85 + Math.random() * 14 : 90 + Math.random() * 9,
      topic: randomTopic.name,
      riskLevel: hasDepressionIndicators ?
        (Math.random() > 0.5 ? 'high' : 'medium') : 'low',
      highlightedText: hasDepressionIndicators ? inputText.split(' ')
        .filter(w => ['cô đơn', 'mệt mỏi', 'áp lực', 'vô nghĩa', 'buồn', 'không muốn'].some(d => w.includes(d)))
        .join(' ') : undefined,
      explanation: hasDepressionIndicators ?
        `Model nhận diện các cụm từ liên quan đến ${randomTopic.name.toLowerCase()}, ` +
        `một trong những chủ đề phổ biến trong các văn bản thể hiện dấu hiệu trầm cảm.` :
        'Văn bản không chứa các chỉ báo rõ ràng về trầm cảm.',
    });

    setIsLoading(false);
  };

  const confidenceBars = [
    { label: 'Normal', value: result ? (result.prediction === 'normal' ? result.confidence : 100 - result.confidence) : 0, color: 'bg-normal' },
    { label: 'Depression', value: result ? (result.prediction === 'depression' ? result.confidence : 100 - result.confidence) : 0, color: 'bg-depression' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <section className="text-center space-y-2">
        <h1 className="font-display text-3xl font-bold text-dark">
          Text Analysis
        </h1>
        <p className="text-muted">
          Enter Vietnamese text to analyze for depression indicators
        </p>
      </section>

      {/* Input Section */}
      <Card>
        <CardContent className="p-8">
          <label className="block text-sm font-medium text-dark mb-3">
            Input Text
          </label>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Nhập văn bản tiếng Việt để phân tích..."
            className="input-field min-h-[150px] resize-y font-body"
          />
          <div className="flex justify-between items-center mt-4">
            <p className="text-sm text-muted">
              {inputText.length} characters
            </p>
            <Button
              onClick={handlePredict}
              isLoading={isLoading}
              disabled={!inputText.trim()}
              size="lg"
            >
              <Brain className="w-5 h-5" />
              Analyze
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results Section */}
      {result && (
        <div className="space-y-6 animate-slide-up">
          {/* Main Result Card */}
          <Card className={cn(
            'overflow-hidden',
            result.prediction === 'depression' ? 'ring-2 ring-depression/20' : 'ring-2 ring-normal/20'
          )}>
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
                    <h3 className={cn(
                      'font-display text-3xl font-bold',
                      result.prediction === 'depression' ? 'text-depression' : 'text-normal'
                    )}>
                      {result.prediction === 'depression' ? 'Depression' : 'Normal'}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      <TrendingUp className="w-4 h-4 text-muted" />
                      <span className="text-muted">
                        Confidence: <span className="font-mono font-semibold text-dark">{result.confidence.toFixed(1)}%</span>
                      </span>
                    </div>
                  </div>
                </div>

                {/* Risk Badge */}
                <div className={cn(
                  'px-4 py-2 rounded-full font-semibold text-sm',
                  result.riskLevel === 'high' && 'bg-depression text-white',
                  result.riskLevel === 'medium' && 'bg-amber-100 text-amber-800',
                  result.riskLevel === 'low' && 'bg-normal text-white',
                )}>
                  Risk: {result.riskLevel.charAt(0).toUpperCase() + result.riskLevel.slice(1)}
                </div>
              </div>

              {/* Confidence Bars */}
              <div className="space-y-3">
                {confidenceBars.map((bar) => (
                  <div key={bar.label}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-muted">{bar.label}</span>
                      <span className="font-mono font-medium">{bar.value.toFixed(1)}%</span>
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
            <Card hover>
              <CardContent className="p-6">
                <h4 className="text-sm font-medium text-muted mb-2">Detected Topic</h4>
                <p className="font-display text-xl font-semibold text-primary">
                  {result.topic}
                </p>
              </CardContent>
            </Card>

            <Card hover>
              <CardContent className="p-6">
                <h4 className="text-sm font-medium text-muted mb-2">AI Explanation</h4>
                <p className="text-dark">
                  {result.explanation}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Highlighted Text */}
          {result.highlightedText && (
            <Card>
              <CardContent className="p-6">
                <h4 className="text-sm font-medium text-muted mb-3">Highlighted Keywords</h4>
                <p className="text-lg">
                  {inputText.split(' ').map((word, i) => {
                    const isHighlighted = ['cô đơn', 'mệt mỏi', 'áp lực', 'vô nghĩa', 'buồn', 'không muốn']
                      .some(d => word.includes(d));
                    return (
                      <span
                        key={i}
                        className={cn(
                          'mx-0.5',
                          isHighlighted && 'bg-depression/20 text-depression font-semibold px-1 rounded'
                        )}
                      >
                        {word}{' '}
                      </span>
                    );
                  })}
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
