import React from 'react';
import { AppointmentCard } from '../components/AppointmentCard';
import { Calendar, PlusCircle } from 'lucide-react';

interface AppointmentsProps {
  data: any;
  onRefresh: () => void;
  setActiveTab: (tab: string) => void;
}

export const Appointments: React.FC<AppointmentsProps> = ({ data, onRefresh, setActiveTab }) => {
  const { appointments } = data;

  return (
    <div className="space-y-6">
      {/* Page Header info */}
      <div className="flex justify-between items-center bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
        <div>
          <h2 className="text-base font-bold text-gray-800">Technician House Visits</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            You have <strong className="text-brand-red">{appointments.length}</strong> scheduled or historical appointments on record.
          </p>
        </div>
        <button
          onClick={() => setActiveTab('chat')}
          className="flex items-center gap-1 text-xs font-bold bg-brand-red text-white py-2.5 px-4 rounded-lg hover:bg-brand-redHover transition-colors shadow-sm"
        >
          <PlusCircle className="w-4 h-4" /> Book New Visit
        </button>
      </div>

      {/* Appointment List */}
      {appointments.length > 0 ? (
        <div className="space-y-4">
          {appointments.map((apt: any) => (
            <AppointmentCard 
              key={apt.appointment_id} 
              appointment={apt} 
              onRefresh={onRefresh} 
            />
          ))}
        </div>
      ) : (
        <div className="bg-white border border-gray-100 rounded-2xl p-12 text-center shadow-sm flex flex-col items-center justify-center space-y-3">
          <Calendar className="w-12 h-12 text-gray-300 stroke-[1.5]" />
          <h3 className="font-bold text-gray-800 text-base">No Service Appointments</h3>
          <p className="text-xs text-gray-500 max-w-sm">
            Need a certified technician to inspect your appliance? Open our chatbot diagnostic assistant to book a home visit!
          </p>
          <button
            onClick={() => setActiveTab('chat')}
            className="btn-premium py-2 px-6 text-xs mt-2"
          >
            Open Chat Assistant
          </button>
        </div>
      )}
    </div>
  );
};
