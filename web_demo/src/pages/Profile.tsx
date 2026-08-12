import { useState } from 'react';
import { User, Settings, Shield, LogOut } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function Profile() {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await logout();
      navigate('/login', { replace: true });
    } finally {
      setIsLoggingOut(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto animate-fade-in">
      <h1 className="font-display text-2xl font-bold text-dark mb-8">
        Profile Settings
      </h1>

      {/* User Info Card */}
      <div className="bg-white rounded-2xl shadow-lg border border-slate-100 overflow-hidden mb-6">
        <div className="bg-gradient-to-r from-primary to-primary-light p-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center">
              <User className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">{user?.username}</h2>
              <p className="text-white/80 text-sm capitalize">{user?.role}</p>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
              <User className="w-5 h-5 text-muted" />
            </div>
            <div>
              <p className="text-xs text-muted uppercase tracking-wide">Username</p>
              <p className="font-medium text-dark">{user?.username}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
              <Shield className="w-5 h-5 text-muted" />
            </div>
            <div>
              <p className="text-xs text-muted uppercase tracking-wide">Role</p>
              <p className="font-medium text-dark capitalize">{user?.role}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
              <Settings className="w-5 h-5 text-muted" />
            </div>
            <div>
              <p className="text-xs text-muted uppercase tracking-wide">Member Since</p>
              <p className="font-medium text-dark">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Admin Link */}
      {isAdmin && (
        <button
          onClick={() => navigate('/admin')}
          className="w-full p-4 bg-white rounded-xl border border-slate-200 hover:border-primary hover:bg-primary/5 transition-all flex items-center justify-between mb-6"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
              <Shield className="w-5 h-5 text-accent" />
            </div>
            <div className="text-left">
              <p className="font-medium text-dark">Admin Dashboard</p>
              <p className="text-sm text-muted">View system statistics and manage users</p>
            </div>
          </div>
          <svg className="w-5 h-5 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      )}

      {/* Logout */}
      <button
        onClick={handleLogout}
        disabled={isLoggingOut}
        className="w-full p-4 bg-white rounded-xl border border-red-200 hover:bg-red-50 transition-all flex items-center justify-center gap-2 text-red-600"
      >
        <LogOut className="w-5 h-5" />
        {isLoggingOut ? 'Signing out...' : 'Sign Out'}
      </button>
    </div>
  );
}
