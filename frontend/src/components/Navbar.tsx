import React, { useState } from 'react';
import { Menu, X, LogOut, MessageSquare, Calendar, Package, User, Sparkles, Phone } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  user: any;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, user, onLogout }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const menuItems = [
    { id: 'chat', label: 'Assistant Chatbot', icon: MessageSquare },
    { id: 'call_center', label: 'Call Center Agent', icon: Phone },
    { id: 'appointments', label: 'My Appointments', icon: Calendar },
    { id: 'orders', label: 'Track Orders', icon: Package },
    { id: 'profile', label: 'My Profile & Tickets', icon: User },
  ];

  const getPageTitle = () => {
    switch (activeTab) {
      case 'chat': return 'SmartCare Diagnostic Assistant';
      case 'call_center': return 'Voice Call Center';
      case 'appointments': return 'Service Appointments';
      case 'orders': return 'Order Tracking & History';
      case 'profile': return 'My Profile & Support Tickets';
      default: return 'Customer Care Portal';
    }
  };

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
        
        {/* Mobile menu trigger */}
        <div className="flex items-center gap-2 md:hidden">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="text-gray-500 hover:text-gray-700 focus:outline-none"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
          <div className="w-8 h-8 bg-brand-red/10 rounded-lg flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-brand-red" />
          </div>
        </div>

        {/* Desktop Page Title */}
        <h1 className="text-xl font-bold text-gray-800 tracking-tight hidden md:block">
          {getPageTitle()}
        </h1>

        {/* Right side user summary */}
        {user && (
          <div className="flex items-center gap-4">
            <span className="text-xs text-gray-500 hidden sm:inline">
              Support Center: <span className="font-semibold text-gray-700">Online</span>
            </span>
            <div className="h-4 w-[1px] bg-gray-200 hidden sm:block"></div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-brand-red text-white flex items-center justify-center font-bold text-xs shadow-sm">
                {user.full_name ? user.full_name.charAt(0) : 'U'}
              </div>
              <span className="text-sm font-medium text-gray-700 max-w-[120px] truncate">
                {user.full_name}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-gray-100 bg-white px-4 py-3 space-y-1 shadow-inner animate-fade-in">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  setMobileMenuOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive 
                    ? 'bg-brand-red text-white' 
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </button>
            );
          })}
          <hr className="my-2 border-gray-100" />
          <button
            onClick={() => {
              setMobileMenuOpen(false);
              onLogout();
            }}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-brand-red hover:bg-red-50 transition-all duration-150"
          >
            <LogOut className="w-5 h-5" />
            Sign Out
          </button>
        </div>
      )}
    </header>
  );
};
