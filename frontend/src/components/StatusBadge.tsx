import React from 'react';

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const getBadgeStyles = () => {
    const s = status.toLowerCase();
    switch (s) {
      case 'scheduled':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'rescheduled':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'cancelled':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'completed':
      case 'delivered':
      case 'resolved':
      case 'installation completed':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'delayed':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'shipped':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'installation pending':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'open':
        return 'bg-sky-50 text-sky-700 border-sky-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-1.5 rounded-full text-xs font-semibold border ${getBadgeStyles()}`}>
      {status.toUpperCase()}
    </span>
  );
};
