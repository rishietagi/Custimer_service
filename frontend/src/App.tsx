import React, { useState, useEffect } from 'react';
import { Login } from './pages/Login';
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { Dashboard } from './pages/Dashboard';
import { ChatAssistant } from './pages/ChatAssistant';
import { CallCenter } from './pages/CallCenter';
import { Appointments } from './pages/Appointments';
import { Orders } from './pages/Orders';
import { Profile } from './pages/Profile';
import { ListSkeleton } from './components/Skeletons';
import { api } from './services/api';
import { AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [user, setUser] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // 1. Sync User Session on Mount
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.removeItem('user');
      }
    }
  }, []);

  // 2. Fetch User Dashboard Data when User changes or Active Tab refresh is triggered
  const fetchDashboardData = async (uId: string) => {
    setLoading(true);
    setErrorMsg('');
    try {
      const data = await api.users.getDashboard(uId);
      setDashboardData(data);
    } catch (err: any) {
      setErrorMsg('Failed to synchronize profile details. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchDashboardData(user.user_id);
    } else {
      setDashboardData(null);
      setActiveTab('dashboard');
    }
  }, [user]);

  const handleLoginSuccess = (loggedInUser: any) => {
    setUser(loggedInUser);
    localStorage.setItem('user', JSON.stringify(loggedInUser));
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem(`chat_sess_${user?.user_id}`);
    setUser(null);
  };

  const handleRefresh = () => {
    if (user) {
      fetchDashboardData(user.user_id);
    }
  };

  if (!user) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  const renderContent = () => {
    if (loading && !dashboardData) {
      return (
        <div className="py-8">
          <ListSkeleton />
        </div>
      );
    }

    if (errorMsg) {
      return (
        <div className="bg-red-50 text-brand-red text-sm p-4 rounded-xl border border-red-200 flex items-center gap-3 my-6">
          <AlertCircle className="w-5 h-5" />
          <span>{errorMsg}</span>
          <button 
            onClick={handleRefresh}
            className="ml-auto font-bold text-xs underline uppercase hover:text-brand-redHover"
          >
            Retry Sync
          </button>
        </div>
      );
    }

    if (!dashboardData) return null;

    switch (activeTab) {
      case 'dashboard':
        return <Dashboard data={dashboardData} setActiveTab={setActiveTab} />;
      case 'chat':
        return <ChatAssistant user={user} onRefreshDashboard={handleRefresh} />;
      case 'call_center':
        return <CallCenter user={user} onRefreshDashboard={handleRefresh} />;
      case 'appointments':
        return <Appointments data={dashboardData} onRefresh={handleRefresh} setActiveTab={setActiveTab} />;
      case 'orders':
        return <Orders data={dashboardData} onRefresh={handleRefresh} setActiveTab={setActiveTab} />;
      case 'profile':
        return <Profile data={dashboardData} setActiveTab={setActiveTab} />;
      default:
        return <Dashboard data={dashboardData} setActiveTab={setActiveTab} />;
    }
  };

  return (
    <div className="flex bg-[#f8f9fa] min-h-screen">
      {/* Sidebar Navigation */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        user={user} 
        onLogout={handleLogout} 
      />

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navbar */}
        <Navbar 
          activeTab={activeTab} 
          setActiveTab={setActiveTab} 
          user={user} 
          onLogout={handleLogout} 
        />

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 max-w-6xl w-full mx-auto">
          {/* Logo link / Home shortcut */}
          {activeTab !== 'dashboard' && (
            <button
              onClick={() => setActiveTab('dashboard')}
              className="text-xs font-semibold text-gray-500 hover:text-brand-red flex items-center gap-1 mb-4 select-none"
            >
              &larr; Back to Dashboard
            </button>
          )}
          {renderContent()}
        </main>
      </div>
    </div>
  );
};
