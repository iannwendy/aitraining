import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import Dashboard from '@/pages/Dashboard';
import Prediction from '@/pages/Prediction';
import BatchPrediction from '@/pages/BatchPrediction';
import Topics from '@/pages/Topics';
import Statistics from '@/pages/Statistics';
import History from '@/pages/History';
import ModelComparison from '@/pages/ModelComparison';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="prediction" element={<Prediction />} />
          <Route path="batch" element={<BatchPrediction />} />
          <Route path="topics" element={<Topics />} />
          <Route path="statistics" element={<Statistics />} />
          <Route path="history" element={<History />} />
          <Route path="compare" element={<ModelComparison />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
