import React, { useState } from 'react';
import { StatusBadge } from '../components/StatusBadge';
import { Shield, Ticket, MapPin, Mail, Phone, Calendar } from 'lucide-react';

interface ProfileProps {
  data: any;
  setActiveTab: (tab: string) => void;
}

export const Profile: React.FC<ProfileProps> = ({ data, setActiveTab }) => {
  const { user, products, support_cases } = data;
  const [activeSubTab, setActiveSubTab] = useState<'products' | 'tickets'>('products');

  return (
    <div className="space-y-6">
      {/* Account Profile Card */}
      <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-brand-red text-white font-bold flex items-center justify-center text-lg">
            {user.full_name ? user.full_name.charAt(0) : 'U'}
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-800">{user.full_name}</h2>
            <p className="text-xs text-gray-500 font-mono">@{user.username} | Account ID: {user.user_id}</p>
          </div>
        </div>

        <div className="h-[1px] bg-gray-100" />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <Mail className="w-4 h-4 text-gray-400" />
            <span>Email: <strong className="text-gray-800">{user.email}</strong></span>
          </div>
          <div className="flex items-center gap-2">
            <Phone className="w-4 h-4 text-gray-400" />
            <span>Phone: <strong className="text-gray-800">{user.phone}</strong></span>
          </div>
          <div className="flex items-start gap-2 md:col-span-2">
            <MapPin className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
            <div>
              <span>Location Site: <strong className="text-gray-800">{user.address || 'Not provided'}</strong></span>
              {user.city && <p className="text-xs text-gray-500 mt-0.5">{user.city} - {user.pincode}</p>}
            </div>
          </div>
        </div>
      </div>

      {/* Sub Tabs */}
      <div className="flex bg-gray-100 rounded-xl p-1 shrink-0 w-max border border-gray-200">
        <button
          onClick={() => setActiveSubTab('products')}
          className={`py-2 px-4 text-xs font-semibold rounded-lg transition-all ${
            activeSubTab === 'products' 
              ? 'bg-white text-gray-800 shadow-sm' 
              : 'text-gray-500 hover:text-gray-800'
          }`}
        >
          🛡️ Registered Devices
        </button>
        <button
          onClick={() => setActiveSubTab('tickets')}
          className={`py-2 px-4 text-xs font-semibold rounded-lg transition-all ${
            activeSubTab === 'tickets' 
              ? 'bg-white text-gray-800 shadow-sm' 
              : 'text-gray-500 hover:text-gray-800'
          }`}
        >
          🎫 Support Case History
        </button>
      </div>

      {/* Tab Contents */}
      {activeSubTab === 'products' ? (
        <div className="space-y-4 animate-fade-in">
          {products.length > 0 ? (
            products.map((p: any) => (
              <div key={p.product_id} className="bg-white rounded-xl border border-gray-100 border-l-4 border-emerald-600 shadow-sm p-6 hover:shadow-premium transition-all duration-200">
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <h4 className="text-base font-bold text-gray-800">{p.category}</h4>
                    <p className="text-xs text-gray-500 font-mono mt-0.5">Model: {p.model_number}</p>
                  </div>
                  <span className={`text-xs font-bold px-2.5 py-1.5 rounded-full border ${
                    p.warranty_status === 'In Warranty' 
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200' 
                      : 'bg-red-50 text-brand-red border-red-200'
                  }`}>
                    {p.warranty_status.toUpperCase()}
                  </span>
                </div>
                
                <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-gray-500">
                  <p>Serial Number: <code className="font-mono text-gray-800 bg-gray-50 border border-gray-200 px-1 py-0.5 rounded">{p.serial_number}</code></p>
                  <p>Purchase Date: <span className="font-semibold text-gray-700">{p.purchase_date}</span></p>
                  {p.installation_date && (
                    <p className="sm:col-span-2">Installation Date: <span className="font-semibold text-gray-700">{p.installation_date}</span></p>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="bg-white border border-gray-100 rounded-2xl p-12 text-center shadow-sm flex flex-col items-center justify-center space-y-3">
              <Shield className="w-10 h-10 text-gray-300 stroke-[1.5]" />
              <h3 className="font-bold text-gray-800 text-sm">No Appliances Registered</h3>
              <p className="text-xs text-gray-500 max-w-xs mx-auto">
                Registering your appliances gives you quick access to warranty services and guided diagnostic troubleshooting.
              </p>
              <button
                onClick={() => setActiveTab('chat')}
                className="btn-premium py-2 px-6 text-xs mt-2"
              >
                Register Appliance via Chat
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4 animate-fade-in">
          {support_cases.length > 0 ? (
            support_cases.map((t: any) => (
              <div key={t.case_id} className="bg-white rounded-xl border border-gray-100 border-l-4 border-blue-600 shadow-sm p-6 hover:shadow-premium transition-all duration-200 space-y-4">
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <h4 className="text-base font-bold text-gray-800">{t.title}</h4>
                    <p className="text-xs text-gray-400 mt-1">
                      Ref ID: <span className="font-mono text-gray-600">#{t.case_id}</span> | Category: <span className="font-medium text-gray-600">{t.category}</span>
                    </p>
                  </div>
                  <StatusBadge status={t.status} />
                </div>
                
                <p className="text-xs text-gray-600 bg-gray-50 p-3 rounded-lg border border-gray-100 whitespace-pre-line leading-relaxed">
                  {t.description}
                </p>

                <div className="flex items-center gap-1 text-[10px] text-gray-400 font-semibold uppercase tracking-wider pl-1">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>Created: {t.created_at.slice(0, 16).replace('T', ' ')}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="bg-white border border-gray-100 rounded-2xl p-12 text-center shadow-sm flex flex-col items-center justify-center space-y-3">
              <Ticket className="w-10 h-10 text-gray-300 stroke-[1.5]" />
              <h3 className="font-bold text-gray-800 text-sm">No Support Tickets</h3>
              <p className="text-xs text-gray-500 max-w-xs mx-auto">
                All your inquiries, order complaints, and AMC extension ticket logs will appear here.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
