import { useAuth } from '@/contexts/AuthContext';

export default function Profile() {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-foreground">Profile</h1>
      <div className="bg-card p-6 rounded-lg shadow space-y-4">
        <div>
          <label className="text-sm font-medium text-muted-foreground">Username</label>
          <p className="text-lg text-foreground">{user.username}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-muted-foreground">Role</label>
          <p className="text-lg text-foreground capitalize">{user.role}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-muted-foreground">Member Since</label>
          <p className="text-lg text-foreground">
            {new Date(user.created_at).toLocaleDateString()}
          </p>
        </div>
      </div>
      <button
        onClick={handleLogout}
        className="px-4 py-2 text-white bg-red-500 rounded-md hover:bg-red-600"
      >
        Logout
      </button>
    </div>
  );
}
