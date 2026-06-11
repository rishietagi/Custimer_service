import React from 'react';
import { MessageSquare, Calendar, Package, User, LogOut, Sparkles, Phone } from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  user: any;
  onLogout: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, user, onLogout }) => {
  const menuItems = [
    { id: 'chat', label: 'Assistant Chatbot', icon: MessageSquare },
    { id: 'call_center', label: 'Call Center Agent', icon: Phone },
    { id: 'appointments', label: 'My Appointments', icon: Calendar },
    { id: 'orders', label: 'Track Orders', icon: Package },
    { id: 'profile', label: 'My Profile & Tickets', icon: User },
  ];

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen flex flex-col justify-between hidden md:flex">
      <div>
        {/* Brand Header */}
        <div className="p-6 border-b border-gray-100 flex flex-col items-center justify-center">
          <div className="w-12 h-12 bg-brand-red/10 rounded-xl flex items-center justify-center mb-2">
            <Sparkles className="w-6 h-6 text-brand-red" />
          </div>
          <h2 className="text-lg font-bold text-gray-800 tracking-tight">SmartCare</h2>
          <span className="text-[10px] uppercase tracking-wider font-semibold text-gray-400">Support Portal</span>
        </div>

        {/* User Card */}
        {user && (
          <div className="mx-4 my-6 p-4 rounded-xl bg-gray-50 border border-gray-100 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-brand-red text-white font-bold flex items-center justify-center text-sm shadow-sm">
              {user.full_name ? user.full_name.charAt(0) : 'U'}
            </div>
            <div className="overflow-hidden">
              <p className="text-sm font-semibold text-gray-800 truncate">{user.full_name}</p>
              <p className="text-xs text-gray-500 truncate">@{user.username}</p>
            </div>
          </div>
        )}

        {/* Navigation Menu */}
        <nav className="px-3 space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive 
                    ? 'bg-brand-red text-white shadow-premium' 
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-gray-400'}`} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer & Sign Out */}
      <div className="p-4 border-t border-gray-100 space-y-4">
        <button
          onClick={onLogout}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 border border-gray-200 text-gray-600 hover:text-brand-red hover:border-brand-red rounded-lg text-sm font-medium transition-all duration-150 active:scale-[0.98]"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
        <p className="text-center text-[10px] text-gray-400 font-medium">
          © 2026 SmartCare Corp.
        </p>
      </div>
    </aside>
  );
};
