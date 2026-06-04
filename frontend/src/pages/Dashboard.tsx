import React from 'react';
import { Calendar, Package, AlertCircle, MessageSquare, ChevronRight, CheckCircle } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';

interface DashboardProps {
  data: any;
  setActiveTab: (tab: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ data, setActiveTab }) => {
  const { user, products, appointments, orders, support_cases } = data;

  // Filter active appointments (not Cancelled, not Completed)
  const activeAppointments = appointments.filter((apt: any) => 
    apt.status !== 'Cancelled' && apt.status !== 'Completed'
  );
  const nextAppointment = activeAppointments.length > 0 ? activeAppointments[0] : null;

  // Filter open tickets
  const openTickets = support_cases.filter((ticket: any) => ticket.status !== 'Resolved');

  // Filter recent orders
  const recentOrder = orders.length > 0 ? orders[0] : null;

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-brand-red to-pink-800 rounded-2xl p-6 sm:p-8 text-white shadow-lg relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="z-10">
          <h2 className="text-2xl font-bold tracking-tight">Welcome, {user.full_name}!</h2>
          <p className="text-red-100 text-sm mt-1 max-w-md">
            Manage your appliances, check shipping states, or talk to our virtual diagnostic tech.
          </p>
        </div>
        <button
          onClick={() => setActiveTab('chat')}
          className="z-10 bg-white text-brand-red font-semibold py-3 px-6 rounded-xl hover:bg-red-50 hover:shadow-lg active:scale-[0.98] transition-all flex items-center justify-center gap-2 text-sm self-start md:self-auto shrink-0"
        >
          <MessageSquare className="w-4 h-4 fill-brand-red" />
          Talk to Diagnostic Tech
        </button>
        {/* Decorative circle */}
        <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-white/5 rounded-full blur-2xl pointer-events-none"></div>
      </div>

      {/* Grid of Summaries */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Next Scheduled Service Card */}
        <div className="bg-white rounded-xl border border-gray-100 p-6 flex flex-col justify-between shadow-sm space-y-4 hover:shadow-premium transition-all duration-200">
          <div className="flex justify-between items-center">
            <span className="text-xs uppercase tracking-wider font-bold text-gray-400">Next Service Visit</span>
            <Calendar className="w-5 h-5 text-brand-red" />
          </div>
          {nextAppointment ? (
            <div className="space-y-3">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-bold text-gray-800 text-sm">{nextAppointment.product_category}</h4>
                  <p className="text-xs text-gray-500 font-mono">APT #{nextAppointment.appointment_id}</p>
                </div>
                <StatusBadge status={nextAppointment.status} />
              </div>
              <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600 space-y-1 border-l-2 border-brand-red">
                <p>📅 <strong className="text-gray-800">{nextAppointment.preferred_date}</strong></p>
                <p>🕒 <span>{nextAppointment.preferred_time_slot.slice(0, 19)}</span></p>
                <p>👤 <span>Tech: {nextAppointment.technician_name.split(' (')[0]}</span></p>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-6 text-center text-gray-400 space-y-2">
              <Calendar className="w-8 h-8 text-gray-200 stroke-[1.5]" />
              <p className="text-xs">No active repair visits scheduled.</p>
              <button 
                onClick={() => setActiveTab('chat')} 
                className="text-xs font-semibold text-brand-red hover:underline"
              >
                Schedule one now
              </button>
            </div>
          )}
          <button 
            onClick={() => setActiveTab('appointments')}
            className="text-xs font-bold text-brand-red hover:text-brand-redHover flex items-center justify-end gap-1 pt-2 mt-auto"
          >
            Manage Appointments <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Recent Order Status Card */}
        <div className="bg-white rounded-xl border border-gray-100 p-6 flex flex-col justify-between shadow-sm space-y-4 hover:shadow-premium transition-all duration-200">
          <div className="flex justify-between items-center">
            <span className="text-xs uppercase tracking-wider font-bold text-gray-400">Recent Shipment</span>
            <Package className="w-5 h-5 text-brand-red" />
          </div>
          {recentOrder ? (
            <div className="space-y-3">
              <div className="flex justify-between items-start">
                <div className="max-w-[70%]">
                  <h4 className="font-bold text-gray-800 text-sm truncate">{recentOrder.product_name}</h4>
                  <p className="text-xs text-gray-500 font-mono">Order #{recentOrder.order_id}</p>
                </div>
                <StatusBadge status={recentOrder.status} />
              </div>
              <p className="text-xs text-gray-500">Ordered: {recentOrder.created_at.slice(0, 10)}</p>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-6 text-center text-gray-400 space-y-2">
              <Package className="w-8 h-8 text-gray-200 stroke-[1.5]" />
              <p className="text-xs">No orders recorded on this profile.</p>
            </div>
          )}
          <button 
            onClick={() => setActiveTab('orders')}
            className="text-xs font-bold text-brand-red hover:text-brand-redHover flex items-center justify-end gap-1 pt-2 mt-auto"
          >
            Track Shipments <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Support Case Tickets Card */}
        <div className="bg-white rounded-xl border border-gray-100 p-6 flex flex-col justify-between shadow-sm space-y-4 hover:shadow-premium transition-all duration-200">
          <div className="flex justify-between items-center">
            <span className="text-xs uppercase tracking-wider font-bold text-gray-400">Open Tickets</span>
            <AlertCircle className="w-5 h-5 text-brand-red" />
          </div>
          {openTickets.length > 0 ? (
            <div className="space-y-3">
              <div className="flex items-center gap-1.5 text-xs text-brand-red font-semibold">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>{openTickets.length} unresolved support tickets</span>
              </div>
              <div className="space-y-2 max-h-[85px] overflow-y-auto pr-1">
                {openTickets.slice(0, 2).map((ticket: any) => (
                  <div key={ticket.case_id} className="flex justify-between text-xs py-1 border-b border-gray-50">
                    <span className="font-medium text-gray-700 truncate max-w-[70%]">{ticket.title}</span>
                    <span className="font-semibold text-brand-red uppercase font-mono">{ticket.status}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-6 text-center text-gray-400 space-y-2">
              <CheckCircle className="w-8 h-8 text-emerald-100 stroke-[1.5]" />
              <p className="text-xs text-emerald-800">All tickets resolved successfully!</p>
            </div>
          )}
          <button 
            onClick={() => setActiveTab('profile')}
            className="text-xs font-bold text-brand-red hover:text-brand-redHover flex items-center justify-end gap-1 pt-2 mt-auto"
          >
            View Ticket Log <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

      </div>

      {/* Grid: Quick Info & Devices Summary */}
      <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
        <h3 className="text-base font-bold text-gray-800 mb-4">My Registered Appliances</h3>
        {products.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {products.map((p: any) => (
              <div key={p.product_id} className="bg-gray-50 border border-gray-100 rounded-xl p-4 flex flex-col justify-between hover:border-gray-200 transition-colors">
                <div>
                  <div className="flex justify-between items-start gap-2">
                    <h4 className="font-bold text-gray-800 text-sm truncate">{p.category}</h4>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      p.warranty_status === 'In Warranty' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-brand-red'
                    }`}>
                      {p.warranty_status.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 font-mono mt-0.5">Model: {p.model_number}</p>
                </div>
                <p className="text-[11px] text-gray-400 mt-4">S/N: <code className="font-mono bg-white border border-gray-200 px-1 py-0.5 rounded">{p.serial_number}</code></p>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 text-gray-400 text-xs">
            No home appliances registered under this profile. Register one in the Chatbot assistant menu!
          </div>
        )}
      </div>
    </div>
  );
};
