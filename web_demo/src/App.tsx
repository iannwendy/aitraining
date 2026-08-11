import './i18n';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import Dashboard from '@/pages/Dashboard';
import Prediction from '@/pages/Prediction';
import BatchPrediction from '@/pages/BatchPrediction';
import History from '@/pages/History';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="prediction" element={<Prediction />} />
          <Route path="batch" element={<BatchPrediction />} />
          <Route path="history" element={<History />} />
          {/* Hidden routes: Topics, Statistics, Compare - redirect to Dashboard */}
          <Route path="topics" element={<Navigate to="/" replace />} />
          <Route path="statistics" element={<Navigate to="/" replace />} />
          <Route path="compare" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
