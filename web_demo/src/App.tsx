import './i18n';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { AuthProvider } from '@/contexts/AuthContext';
import { ProtectedRoute, PublicRoute } from '@/components/auth/ProtectedRoute';
import Home from '@/pages/Home';
import Prediction from '@/pages/Prediction';
import BatchPrediction from '@/pages/BatchPrediction';
import History from '@/pages/History';
import Login from '@/pages/Login';
import Register from '@/pages/Register';
import Profile from '@/pages/Profile';
import AdminDashboard from '@/pages/AdminDashboard';
import YouTubeAnalysis from '@/pages/YouTubeAnalysis';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route
            path="/login"
            element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            }
          />
          <Route
            path="/register"
            element={
              <PublicRoute>
                <Register />
              </PublicRoute>
            }
          />

          {/* Protected routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Home />} />
            <Route path="prediction" element={<Prediction />} />
            <Route path="batch" element={<BatchPrediction />} />
            <Route path="history" element={<History />} />
            <Route path="youtube" element={<YouTubeAnalysis />} />
            <Route path="profile" element={<Profile />} />
            {/* Hidden routes */}
            <Route path="topics" element={<Navigate to="/" replace />} />
            <Route path="statistics" element={<Navigate to="/" replace />} />
            <Route path="compare" element={<Navigate to="/" replace />} />
          </Route>

          {/* Admin routes */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute requireAdmin>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<AdminDashboard />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
