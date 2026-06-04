import React, { useState } from 'react';
import { api } from '../services/api';
import { OrderTimeline } from '../components/OrderTimeline';
import { StatusBadge } from '../components/StatusBadge';
import { Search, PhoneCall, AlertTriangle, Hammer, CheckCircle, AlertCircle } from 'lucide-react';

interface OrdersProps {
  data: any;
  onRefresh: () => void;
  setActiveTab: (tab: string) => void;
}

export const Orders: React.FC<OrdersProps> = ({ data, onRefresh, setActiveTab }) => {
  const { user, orders } = data;
  const [activeSubTab, setActiveSubTab] = useState<'my' | 'lookup'>('my');

  // Lookup state
  const [lookupId, setLookupId] = useState('');
  const [lookupContact, setLookupContact] = useState('');
  const [lookupResult, setLookupResult] = useState<any>(null);
  const [lookupError, setLookupError] = useState('');
  const [lookupLoading, setLookupLoading] = useState(false);

  // Card Action States
  // Tracks active action per order card using a dictionary: { [orderId]: 'callback' | 'escalate' | 'complaint' | 'install' | 'idle' }
  const [cardActions, setCardActions] = useState<Record<string, string>>({});
  const [complaintSubj, setComplaintSubj] = useState('');
  const [complaintDesc, setComplaintDesc] = useState('');
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  const [successInfo, setSuccessInfo] = useState<Record<string, string>>({});

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lookupId || !lookupContact) {
      setLookupError('Please enter both Order ID and Phone/Email.');
      return;
    }
    setLookupLoading(true);
    setLookupError('');
    setLookupResult(null);
    try {
      const res = await api.orders.lookup(lookupId, lookupContact);
      setLookupResult(res);
    } catch (err: any) {
      setLookupError(err.response?.data?.detail || 'No order found matching details. Try ORD-1153 with jane.smith@support-example.com');
    } finally {
      setLookupLoading(false);
    }
  };

  const handleCardAction = (orderId: string, action: string) => {
    setCardActions(prev => ({ ...prev, [orderId]: action }));
    setSuccessInfo(prev => {
      const next = { ...prev };
      delete next[orderId];
      return next;
    });
    setComplaintSubj('');
    setComplaintDesc('');
  };

  const submitCallback = async (orderId: string) => {
    setActionLoading(prev => ({ ...prev, [orderId]: true }));
    try {
      const res = await api.orders.requestCallback(orderId, user.user_id);
      setSuccessInfo(prev => ({ ...prev, [orderId]: res.message }));
    } catch (err: any) {
      setSuccessInfo(prev => ({ ...prev, [orderId]: 'Failed to request callback.' }));
    } finally {
      setActionLoading(prev => ({ ...prev, [orderId]: false }));
    }
  };

  const submitEscalate = async (orderId: string) => {
    setActionLoading(prev => ({ ...prev, [orderId]: true }));
    try {
      const res = await api.orders.escalate(orderId, user.user_id);
      setSuccessInfo(prev => ({ ...prev, [orderId]: `🚀 Issue Escalated! Support Ticket Reference ID: ${res.case_id}` }));
      onRefresh();
    } catch (err: any) {
      setSuccessInfo(prev => ({ ...prev, [orderId]: 'Failed to escalate issue.' }));
    } finally {
      setActionLoading(prev => ({ ...prev, [orderId]: false }));
    }
  };

  const submitComplaint = async (e: React.FormEvent, orderId: string) => {
    e.preventDefault();
    if (!complaintSubj || !complaintDesc) return;
    setActionLoading(prev => ({ ...prev, [orderId]: true }));
    try {
      const res = await api.orders.submitComplaint(orderId, user.user_id, complaintSubj, complaintDesc);
      setSuccessInfo(prev => ({ ...prev, [orderId]: `✅ Ticket Submitted successfully. Reference ID: ${res.case_id}` }));
      setCardActions(prev => ({ ...prev, [orderId]: 'idle' }));
      onRefresh();
    } catch (err: any) {
      alert('Failed to submit complaint ticket.');
    } finally {
      setActionLoading(prev => ({ ...prev, [orderId]: false }));
    }
  };

  const renderOrderCard = (order: any) => {
    const activeAction = cardActions[order.order_id] || 'idle';
    const isActionLoading = actionLoading[order.order_id] || false;
    const successMsg = successInfo[order.order_id] || '';

    const installDisabled = !['Delivered', 'Installation Pending'].includes(order.status);

    return (
      <div key={order.order_id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 hover:shadow-premium hover:border-gray-200 transition-all duration-200 space-y-4">
        {/* Header */}
        <div className="flex justify-between items-start gap-4">
          <div>
            <h3 className="text-base font-bold text-gray-800">
              Order <span className="text-brand-red font-mono">#{order.order_id}</span>
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">
              Product: <span className="font-semibold text-gray-700">{order.product_name}</span>
            </p>
          </div>
          <StatusBadge status={order.status} />
        </div>

        <p className="text-xs text-gray-400">Ordered On: <span className="font-medium text-gray-600">{order.created_at.slice(0, 10)}</span></p>

        {/* Delivery Progress Timeline */}
        <div className="bg-gray-50/50 p-4 rounded-xl border border-gray-100">
          <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">Delivery Status Timeline</p>
          <OrderTimeline status={order.status} />
        </div>

        {/* Success Banner Info */}
        {successMsg && (
          <div className="bg-emerald-50 text-emerald-800 text-xs p-3 rounded-lg border border-emerald-200 flex items-start gap-2">
            <CheckCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Action Panel Forms */}
        {activeAction === 'callback' && !successMsg && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-2">
            <h4 className="text-xs font-bold text-blue-900 flex items-center gap-1">
              <PhoneCall className="w-3.5 h-3.5" /> Confirm Callback Request
            </h4>
            <p className="text-xs text-blue-700">We will call you at your registered phone number <strong className="text-blue-900">{order.registered_phone}</strong>.</p>
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => submitCallback(order.order_id)}
                disabled={isActionLoading}
                className="bg-blue-700 hover:bg-blue-800 text-white font-semibold text-xs py-1.5 px-3 rounded-lg disabled:opacity-50"
              >
                {isActionLoading ? 'Submitting...' : 'Request Call'}
              </button>
              <button
                onClick={() => handleCardAction(order.order_id, 'idle')}
                className="bg-white text-blue-800 font-semibold text-xs py-1.5 px-3 rounded-lg border border-blue-200"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {activeAction === 'escalate' && !successMsg && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-2">
            <h4 className="text-xs font-bold text-amber-950 flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" /> Escalate Shipment Delay
            </h4>
            <p className="text-xs text-amber-800">This raises a high priority support case. A supervisor will review and contact you via email.</p>
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => submitEscalate(order.order_id)}
                disabled={isActionLoading}
                className="bg-amber-700 hover:bg-amber-800 text-white font-semibold text-xs py-1.5 px-3 rounded-lg"
              >
                {isActionLoading ? 'Escalating...' : 'Confirm Escalation'}
              </button>
              <button
                onClick={() => handleCardAction(order.order_id, 'idle')}
                className="bg-white text-amber-800 font-semibold text-xs py-1.5 px-3 rounded-lg border border-amber-200"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {activeAction === 'complaint' && !successMsg && (
          <form onSubmit={(e) => submitComplaint(e, order.order_id)} className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
            <h4 className="text-xs font-bold text-gray-800">Raise Complaint Ticket</h4>
            <div className="space-y-2">
              <input
                type="text"
                required
                placeholder="Complaint Subject (e.g. Package damaged)"
                value={complaintSubj}
                onChange={(e) => setComplaintSubj(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2 text-xs focus:outline-none"
              />
              <textarea
                required
                placeholder="Provide detailed description of order complaint..."
                value={complaintDesc}
                onChange={(e) => setComplaintDesc(e.target.value)}
                className="w-full bg-white border border-gray-200 rounded-lg p-2 text-xs focus:outline-none h-16"
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={isActionLoading}
                className="bg-brand-red text-white font-semibold text-xs py-1.5 px-3 rounded-lg hover:bg-brand-redHover disabled:opacity-50"
              >
                {isActionLoading ? 'Submitting...' : 'Submit Case'}
              </button>
              <button
                type="button"
                onClick={() => handleCardAction(order.order_id, 'idle')}
                className="bg-white text-gray-700 font-semibold text-xs py-1.5 px-3 rounded-lg border border-gray-200"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {activeAction === 'install' && !successMsg && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 space-y-2 text-xs text-purple-800">
            <h4 className="font-bold text-purple-950 flex items-center gap-1">
              <Hammer className="w-3.5 h-3.5" /> Schedule Product Installation
            </h4>
            <p>To register and book installation for your new appliance, please head over to the <strong>💬 Chatbot Assistant</strong> and select <strong>Product Help</strong> or <strong>Other Help &gt; Request Installation</strong>.</p>
            <div className="flex gap-2 pt-2">
              <button
                onClick={() => setActiveTab('chat')}
                className="bg-purple-700 hover:bg-purple-800 text-white font-semibold py-1.5 px-3 rounded-lg"
              >
                Go to Assistant Chatbot
              </button>
              <button
                onClick={() => handleCardAction(order.order_id, 'idle')}
                className="bg-white text-purple-900 border border-purple-200 font-semibold py-1.5 px-3 rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        )}

        {/* Primary buttons panel */}
        {activeAction === 'idle' && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-gray-50">
            <button
              onClick={() => handleCardAction(order.order_id, 'complaint')}
              className="text-xs font-semibold py-2 px-3 rounded-lg bg-gray-50 hover:bg-gray-100 text-gray-700 transition-colors text-center border border-gray-200"
            >
              ⚠️ Complaint
            </button>
            <button
              onClick={() => handleCardAction(order.order_id, 'callback')}
              className="text-xs font-semibold py-2 px-3 rounded-lg bg-gray-50 hover:bg-gray-100 text-gray-700 transition-colors text-center border border-gray-200"
            >
              📞 Callback
            </button>
            <button
              onClick={() => handleCardAction(order.order_id, 'escalate')}
              className="text-xs font-semibold py-2 px-3 rounded-lg bg-gray-50 hover:bg-gray-100 text-gray-700 transition-colors text-center border border-gray-200"
            >
              🚀 Escalate
            </button>
            <button
              disabled={installDisabled}
              onClick={() => handleCardAction(order.order_id, 'install')}
              className="text-xs font-semibold py-2 px-3 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 transition-colors text-center disabled:opacity-40 disabled:pointer-events-none"
            >
              🛠️ Install
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Sub Tabs Toggle */}
      <div className="flex bg-gray-100 rounded-xl p-1 shrink-0 w-max border border-gray-200">
        <button
          onClick={() => setActiveSubTab('my')}
          className={`py-2 px-4 text-xs font-semibold rounded-lg transition-all ${
            activeSubTab === 'my' 
              ? 'bg-white text-gray-800 shadow-sm' 
              : 'text-gray-500 hover:text-gray-800'
          }`}
        >
          🛒 My Purchases
        </button>
        <button
          onClick={() => setActiveSubTab('lookup')}
          className={`py-2 px-4 text-xs font-semibold rounded-lg transition-all ${
            activeSubTab === 'lookup' 
              ? 'bg-white text-gray-800 shadow-sm' 
              : 'text-gray-500 hover:text-gray-800'
          }`}
        >
          🔍 Search Any Order
        </button>
      </div>

      {activeSubTab === 'my' ? (
        <div className="space-y-4 animate-fade-in">
          {orders.length > 0 ? (
            orders.map((order: any) => renderOrderCard(order))
          ) : (
            <div className="bg-white border border-gray-100 rounded-2xl p-12 text-center shadow-sm">
              <p className="text-gray-400 text-sm font-semibold">No purchase orders found on your profile.</p>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4 animate-fade-in">
          {/* General Lookup Form */}
          <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
            <h3 className="text-sm font-bold text-gray-800 mb-4">Track an order using Order ID and contact details:</h3>
            <form onSubmit={handleLookup} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-gray-600">Order ID *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. ORD-1153"
                  value={lookupId}
                  onChange={(e) => setLookupId(e.target.value)}
                  className="w-full bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-sm focus:outline-none focus:bg-white focus:ring-2 focus:ring-brand-red focus:border-transparent transition-all"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-gray-600">Registered Phone or Email *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. jane.smith@support-example.com"
                  value={lookupContact}
                  onChange={(e) => setLookupContact(e.target.value)}
                  className="w-full bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-sm focus:outline-none focus:bg-white focus:ring-2 focus:ring-brand-red focus:border-transparent transition-all"
                />
              </div>
              <button 
                type="submit" 
                disabled={lookupLoading}
                className="btn-premium py-2.5 col-span-1 sm:col-span-2 flex items-center justify-center gap-2 mt-2"
              >
                {lookupLoading ? 'Searching...' : (
                  <>
                    <Search className="w-4 h-4" /> Search Order
                  </>
                )}
              </button>
            </form>

            {lookupError && (
              <div className="bg-red-50 text-brand-red text-xs p-3 rounded-lg border border-red-200 mt-4 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{lookupError}</span>
              </div>
            )}
          </div>

          {/* Search Result */}
          {lookupResult && (
            <div className="space-y-2">
              <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider pl-1">Search Result</h3>
              {renderOrderCard(lookupResult)}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
