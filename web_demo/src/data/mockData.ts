import {
  DashboardStats,
  Topic,
  PredictionResult,
  WordCloudItem,
  BatchPredictionResult
} from '@/types';

export const dashboardStats: DashboardStats = {
  totalComments: 102847,
  totalPredictions: 24856,
  currentModel: 'PhoBERT + BERTopic',
  trainingDate: '2024-06-15',
  metrics: {
    accuracy: 94.2,
    macroF1: 93.5,
    weightedF1: 94.1,
    precision: 93.8,
    recall: 93.2,
  },
};

export const topics: Topic[] = [
  {
    id: 1,
    name: 'Loneliness',
    keywords: ['cô đơn', 'một mình', 'không ai', 'lạc lõng', 'bơ vơ'],
    count: 15234,
    percentage: 28.5,
    examples: [
      'Tôi cảm thấy cô đơn trong căn phòng tối',
      'Không ai hiểu tôi cả',
      'Mỗi đêm chỉ có bóng tối陪伴',
    ],
  },
  {
    id: 2,
    name: 'Academic Stress',
    keywords: ['học tập', 'áp lực', 'thi cử', 'điểm số', 'bài tập'],
    count: 12876,
    percentage: 24.1,
    examples: [
      'Áp lực thi cử kinh khủng quá',
      'Điểm số không như mong đợi',
      'Bài tập chất đống không làm xuể',
    ],
  },
  {
    id: 3,
    name: 'Family Pressure',
    keywords: ['gia đình', 'cha mẹ', 'kỳ vọng', 'hiểu lầm', 'xung đột'],
    count: 8934,
    percentage: 16.7,
    examples: [
      'Bố mẹ kỳ vọng quá nhiều ở tôi',
      'Không ai lắng nghe tôi',
      'Cãi nhau với mẹ suốt ngày',
    ],
  },
  {
    id: 4,
    name: 'Relationship Issues',
    keywords: ['tình yêu', ' chia ly', 'đổ vỡ', 'giận hờn', 'buồn'],
    count: 7234,
    percentage: 13.5,
    examples: [
      'Chia tay rồi, không biết làm sao',
      'Anh ấy không còn yêu tôi nữa',
      'Trái tim tan vỡ',
    ],
  },
  {
    id: 5,
    name: 'Burnout',
    keywords: ['mệt mỏi', 'kiệt sức', 'không muốn', 'bỏ cuộc', 'chán'],
    count: 6845,
    percentage: 12.8,
    examples: [
      'Tôi mệt mỏi với tất cả',
      'Không muốn làm gì nữa',
      'Cuộc sống thật vô nghĩa',
    ],
  },
  {
    id: 6,
    name: 'Self-Worth',
    keywords: ['vô dụng', 'tệ hại', 'xấu xí', 'không xứng', 'ghét'],
    count: 3245,
    percentage: 6.1,
    examples: [
      'Tôi cảm thấy mình vô dụng',
      'Không ai cần tôi',
      'Tôi thật tệ hại',
    ],
  },
];

export const modelComparisons = [
  {
    name: 'TF-IDF + SVM',
    accuracy: 82.0,
    macroF1: 81.0,
    weightedF1: 83.0,
    precision: 80.5,
    recall: 81.5,
    in_domain_f1: 0.81,
    cross_domain_f1: 0.38,
    model_type: 'baseline' as const,
    note: undefined,
  },
  {
    name: 'BiLSTM',
    accuracy: 87.0,
    macroF1: 86.0,
    weightedF1: 88.0,
    precision: 85.5,
    recall: 86.5,
    in_domain_f1: 0.86,
    cross_domain_f1: 0.47,
    model_type: 'bilstm' as const,
    note: undefined,
  },
  {
    name: 'PhoBERT',
    accuracy: 92.0,
    macroF1: 91.0,
    weightedF1: 92.0,
    precision: 90.5,
    recall: 91.5,
    in_domain_f1: 0.91,
    cross_domain_f1: 0.39,
    model_type: 'phobert' as const,
    note: undefined,
  },
  {
    name: 'PhoBERT + BERTopic',
    accuracy: 94.2,
    macroF1: 93.5,
    weightedF1: 94.1,
    precision: 93.8,
    recall: 93.2,
    in_domain_f1: 0.935,
    cross_domain_f1: 0.441,
    model_type: 'hybrid' as const,
    note: undefined,
  },
];

export const predictionHistory: PredictionResult[] = [
  {
    id: '1',
    text: 'Tôi cảm thấy mọi thứ thật vô nghĩa.',
    prediction: 'depression',
    confidence: 96,
    topic: 'Loneliness',
    riskLevel: 'high',
    timestamp: new Date('2024-06-20T10:30:00'),
  },
  {
    id: '2',
    text: 'Hôm nay làm bài kiểm tra rất tốt!',
    prediction: 'normal',
    confidence: 98,
    topic: 'Academic Stress',
    riskLevel: 'low',
    timestamp: new Date('2024-06-20T10:25:00'),
  },
  {
    id: '3',
    text: 'Áp lực học tập thật kinh khủng.',
    prediction: 'depression',
    confidence: 87,
    topic: 'Academic Stress',
    riskLevel: 'medium',
    timestamp: new Date('2024-06-20T10:20:00'),
  },
  {
    id: '4',
    text: 'Gia đình tôi rất hạnh phúc.',
    prediction: 'normal',
    confidence: 95,
    riskLevel: 'low',
    timestamp: new Date('2024-06-20T10:15:00'),
  },
  {
    id: '5',
    text: 'Tôi không còn muốn sống nữa.',
    prediction: 'depression',
    confidence: 99,
    topic: 'Self-Worth',
    riskLevel: 'high',
    timestamp: new Date('2024-06-20T10:10:00'),
  },
];

export const wordCloudData: WordCloudItem[] = [
  { text: 'cô đơn', value: 85, color: '#EF4444' },
  { text: 'áp lực', value: 78, color: '#F97316' },
  { text: 'mệt mỏi', value: 72, color: '#EF4444' },
  { text: 'buồn', value: 68, color: '#EF4444' },
  { text: 'tuyệt vọng', value: 65, color: '#EF4444' },
  { text: 'vô nghĩa', value: 58, color: '#F97316' },
  { text: 'không muốn', value: 55, color: '#F97316' },
  { text: 'hạnh phúc', value: 25, color: '#22C55E' },
  { text: 'vui vẻ', value: 22, color: '#22C55E' },
  { text: 'bình thường', value: 20, color: '#22C55E' },
  { text: 'bạn bè', value: 18, color: '#0D9488' },
  { text: 'gia đình', value: 15, color: '#0D9488' },
];

export const batchResults: BatchPredictionResult[] = [
  { comment: 'Tôi rất cô đơn.', prediction: 'depression', confidence: 0.94, topic: 'Loneliness' },
  { comment: 'Video hay quá!', prediction: 'normal', confidence: 0.98, topic: undefined },
  { comment: 'Áp lực học tập thật kinh khủng.', prediction: 'depression', confidence: 0.89, topic: 'Academic Stress' },
  { comment: 'Hôm nay trời đẹp quá.', prediction: 'normal', confidence: 0.99, topic: undefined },
  { comment: 'Không ai hiểu tôi cả.', prediction: 'depression', confidence: 0.91, topic: 'Loneliness' },
];

export const confusionMatrix = {
  trueNegatives: 8923,
  falsePositives: 456,
  falseNegatives: 234,
  truePositives: 6789,
};
