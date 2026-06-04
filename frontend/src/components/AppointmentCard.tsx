import React, { useState } from 'react';
import { Calendar, Clock, MapPin, User, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { api } from '../services/api';

interface AppointmentCardProps {
  appointment: any;
  onRefresh: () => void;
}

export const AppointmentCard: React.FC<AppointmentCardProps> = ({ appointment, onRefresh }) => {
  const [showMoreInfo, setShowMoreInfo] = useState(false);
  const [actionState, setActionState] = useState<'idle' | 'reschedule' | 'cancel'>('idle');
  const [newDate, setNewDate] = useState('');
  const [newSlot, setNewSlot] = useState('09:00 AM - 12:00 PM (Morning)');
  const [errorMsg, setErrorMsg] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const timeSlots = [
    "09:00 AM - 12:00 PM (Morning)",
    "12:00 PM - 03:00 PM (Afternoon)",
    "03:00 PM - 06:00 PM (Evening)"
  ];

  const handleCancel = async () => {
    setSubmitting(true);
    setErrorMsg('');
    try {
      await api.appointments.cancel(appointment.appointment_id);
      setActionState('idle');
      onRefresh();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to cancel appointment.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReschedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDate) {
      setErrorMsg('Please select a date.');
      return;
    }
    setSubmitting(true);
    setErrorMsg('');
    try {
      await api.appointments.reschedule(appointment.appointment_id, newDate, newSlot);
      setActionState('idle');
      onRefresh();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to reschedule appointment.');
    } finally {
      setSubmitting(false);
    }
  };

  const isCancelled = appointment.status === 'Cancelled';
  const isCompleted = appointment.status === 'Completed';
  const disableActions = isCancelled || isCompleted;

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 hover:shadow-premium hover:border-gray-200 transition-all duration-200 space-y-4">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-base font-bold text-gray-800">
            Appointment <span className="text-brand-red font-mono">#{appointment.appointment_id}</span>
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Assigned: <span className="font-medium text-gray-700">{appointment.technician_name}</span>
          </p>
        </div>
        <StatusBadge status={appointment.status} />
      </div>

      {/* Main Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-gray-600">
        <div className="flex items-center gap-2">
          <User className="w-4 h-4 text-gray-400" />
          <span>Customer: <strong className="text-gray-800">{appointment.customer_name}</strong></span>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray-400" />
          <span>Date: <strong className="text-gray-800">{appointment.preferred_date}</strong></span>
        </div>
        <div className="flex items-center gap-2 col-span-1 md:col-span-2">
          <Clock className="w-4 h-4 text-gray-400" />
          <span>Time: <strong className="text-gray-800">{appointment.preferred_time_slot}</strong></span>
        </div>
      </div>

      {/* Appliance & Issue */}
      <div className="bg-gray-50 rounded-lg p-3 text-sm">
        <p className="text-gray-500 font-medium text-xs uppercase tracking-wider">Appliance & Symptom</p>
        <p className="font-semibold text-gray-800 mt-1">
          {appointment.product_category} <span className="font-mono text-xs font-normal bg-white py-0.5 px-1.5 rounded border border-gray-200 ml-1.5">Model: {appointment.product_model}</span>
        </p>
        <p className="text-gray-600 mt-1 italic">
          &ldquo;{appointment.issue_description}&rdquo;
        </p>
      </div>

      {/* Divider */}
      <div className="h-[1px] bg-gray-100" />

      {/* Primary Action Row */}
      <div className="flex flex-wrap gap-2 items-center justify-between">
        <button
          onClick={() => setShowMoreInfo(!showMoreInfo)}
          className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-gray-800 bg-gray-50 hover:bg-gray-100 py-1.5 px-3 rounded-lg transition-colors"
        >
          {showMoreInfo ? (
            <>
              <ChevronUp className="w-3.5 h-3.5" /> Less Info
            </>
          ) : (
            <>
              <ChevronDown className="w-3.5 h-3.5" /> More Info
            </>
          )}
        </button>

        <div className="flex gap-2">
          <button
            disabled={disableActions}
            onClick={() => setActionState(actionState === 'reschedule' ? 'idle' : 'reschedule')}
            className="text-xs font-semibold text-amber-700 bg-amber-50 hover:bg-amber-100 disabled:opacity-40 disabled:pointer-events-none py-1.5 px-3 rounded-lg transition-colors border border-amber-200"
          >
            Reschedule
          </button>
          <button
            disabled={disableActions}
            onClick={() => setActionState(actionState === 'cancel' ? 'idle' : 'cancel')}
            className="text-xs font-semibold text-brand-red bg-red-50 hover:bg-red-100 disabled:opacity-40 disabled:pointer-events-none py-1.5 px-3 rounded-lg transition-colors border border-red-200"
          >
            Cancel Visit
          </button>
        </div>
      </div>

      {/* Error Message */}
      {errorMsg && (
        <div className="bg-red-50 text-brand-red text-xs p-3 rounded-lg flex items-center gap-2 border border-red-200">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Expandable: More Info */}
      {showMoreInfo && (
        <div className="bg-gray-50 rounded-lg p-4 text-xs grid grid-cols-1 md:grid-cols-2 gap-4 border-l-4 border-brand-red animate-fade-in">
          <div className="space-y-1.5">
            <h4 className="font-bold text-gray-700 text-sm uppercase tracking-wider mb-2">Device Info</h4>
            <p className="text-gray-500">Serial Number: <code className="font-mono text-gray-800 text-sm bg-white px-1.5 py-0.5 rounded border border-gray-200">{appointment.serial_number}</code></p>
            <p className="text-gray-500">Purchase Date: <span className="font-medium text-gray-800">{appointment.purchase_date}</span></p>
            <p className="text-gray-500">Warranty: <span className="font-semibold text-emerald-700">{appointment.warranty_status}</span></p>
            <p className="text-gray-500">Created: <span className="font-medium text-gray-800">{appointment.created_at?.slice(0, 16).replace('T', ' ')}</span></p>
          </div>
          <div className="space-y-1.5">
            <h4 className="font-bold text-gray-700 text-sm uppercase tracking-wider mb-2">Service Site</h4>
            <div className="flex gap-1.5 items-start text-gray-600">
              <MapPin className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-gray-800">{appointment.address}</p>
                <p className="text-gray-500">{appointment.city} - {appointment.pincode}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Expandable Action: Reschedule Form */}
      {actionState === 'reschedule' && (
        <form onSubmit={handleReschedule} className="bg-amber-50/50 border border-amber-200 rounded-lg p-4 space-y-4 animate-fade-in">
          <h4 className="text-sm font-bold text-amber-900">Select New Schedule Visit</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-amber-800 mb-1.5">Preferred Date</label>
              <input
                type="date"
                required
                min={new Date().toISOString().split('T')[0]}
                value={newDate}
                onChange={(e) => setNewDate(e.target.value)}
                className="w-full bg-white text-gray-800 border border-amber-200 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-amber-800 mb-1.5">Preferred Time Slot</label>
              <select
                value={newSlot}
                onChange={(e) => setNewSlot(e.target.value)}
                className="w-full bg-white text-gray-800 border border-amber-200 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                {timeSlots.map((slot) => (
                  <option key={slot} value={slot}>{slot}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={submitting}
              className="bg-amber-700 hover:bg-amber-800 text-white font-semibold text-xs py-2 px-4 rounded-lg transition-colors disabled:opacity-50"
            >
              {submitting ? 'Updating...' : 'Confirm Reschedule'}
            </button>
            <button
              type="button"
              onClick={() => setActionState('idle')}
              className="bg-white hover:bg-gray-100 text-amber-800 font-semibold text-xs py-2 px-4 rounded-lg border border-amber-200 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Expandable Action: Cancel Confirmation */}
      {actionState === 'cancel' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 space-y-3 animate-fade-in">
          <h4 className="text-sm font-bold text-red-900">Are you sure you want to cancel this appointment?</h4>
          <p className="text-xs text-red-700">This action cannot be undone. Our technician dispatch will be recalled.</p>
          <div className="flex gap-2">
            <button
              onClick={handleCancel}
              disabled={submitting}
              className="bg-brand-red hover:bg-brand-redHover text-white font-semibold text-xs py-2 px-4 rounded-lg transition-colors disabled:opacity-50"
            >
              {submitting ? 'Cancelling...' : 'Yes, Cancel Visit'}
            </button>
            <button
              onClick={() => setActionState('idle')}
              className="bg-white hover:bg-gray-100 text-red-800 font-semibold text-xs py-2 px-4 rounded-lg border border-red-200 transition-colors"
            >
              No, Keep Visit
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
