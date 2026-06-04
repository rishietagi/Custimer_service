import React from 'react';
import { Check, Circle, AlertTriangle } from 'lucide-react';

interface OrderTimelineProps {
  status: string;
}

export const OrderTimeline: React.FC<OrderTimelineProps> = ({ status }) => {
  const steps = [
    { title: 'Order Confirmed', desc: 'We have received your order.' },
    { title: 'Shipped', desc: 'Your order has left our regional warehouse.' },
    { title: 'Out for Delivery', desc: 'A local courier is delivering your product today.' },
    { title: 'Delivered', desc: 'The package was signed and delivered.' },
    { title: 'Installation Pending', desc: 'Our installation team will contact you.' },
    { title: 'Installation Completed', desc: 'Product was successfully set up.' },
  ];

  // Find index
  let statusIndex = -1;
  const upperStatus = status.toUpperCase();
  for (let i = 0; i < steps.length; i++) {
    if (upperStatus === steps[i].title.toUpperCase()) {
      statusIndex = i;
      break;
    }
  }

  // Check special cases
  const isDelayed = status.toLowerCase() === 'delayed';

  return (
    <div className="relative pl-6 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-[2px] before:bg-gray-200">
      {steps.map((step, idx) => {
        let stepClass = 'relative flex gap-4';
        let iconContent = <Circle className="w-3 h-3 text-gray-400 fill-gray-400" />;
        let circleBg = 'bg-white border-2 border-gray-300 text-gray-400';
        let stepTitle = step.title;
        let stepDesc = step.desc;

        if (isDelayed && idx === 2) {
          // Out for Delivery represents the delay node
          stepTitle = `${step.title} (Delayed)`;
          stepDesc = 'Your shipment was delayed due to route congestion. We will update you shortly.';
          circleBg = 'bg-amber-100 border-2 border-brand-warning text-brand-warning ring-4 ring-amber-50';
          iconContent = <AlertTriangle className="w-4 h-4 text-brand-warning fill-brand-warning" />;
        } else if (idx < statusIndex) {
          // Completed
          circleBg = 'bg-emerald-600 border-2 border-emerald-600 text-white';
          iconContent = <Check className="w-4 h-4 text-white stroke-[3px]" />;
        } else if (idx === statusIndex) {
          // Active
          circleBg = 'bg-white border-2 border-brand-red text-brand-red ring-4 ring-red-50';
          iconContent = <span className="w-2.5 h-2.5 rounded-full bg-brand-red animate-ping" />;
        }

        return (
          <div key={idx} className={stepClass}>
            {/* Circle Node */}
            <div className={`absolute -left-6 w-6.5 h-6.5 rounded-full flex items-center justify-center z-10 transition-all duration-300 ${circleBg}`}>
              {iconContent}
            </div>

            {/* Content Card */}
            <div className="flex flex-col">
              <span className={`text-sm font-semibold ${idx === statusIndex ? 'text-brand-red' : idx < statusIndex ? 'text-gray-800' : 'text-gray-500'}`}>
                {stepTitle}
              </span>
              <span className="text-xs text-gray-500 mt-0.5">
                {stepDesc}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
