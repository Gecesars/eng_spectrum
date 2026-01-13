import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from '@/pages/auth/Login';
import Register from '@/pages/auth/Register';
import Landing from '@/pages/Landing';
import DashboardLayout from '@/components/layout/DashboardLayout';
import DashboardHome from '@/pages/dashboard/DashboardHome';
import Networks from '@/pages/dashboard/Networks';
import NetworkManager from '@/pages/dashboard/NetworkManager';
import { useAuthStore } from '@/store/useAuthStore';

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected Dashboard Routes */}
        <Route path="/app" element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }>
          <Route index element={<Navigate to="home" replace />} />
          <Route path="home" element={<DashboardHome />} />
          <Route path="networks" element={<Networks />} />
          <Route path="network/:networkId/*" element={<NetworkManager />} />
          <Route path="analysis" element={<div className="text-white p-8">Analysis (Coming Soon)</div>} />
          <Route path="settings" element={<div className="text-white p-8">Settings (Coming Soon)</div>} />
        </Route>

        {/* Root is Landing Page */}
        <Route path="/" element={<Landing />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
