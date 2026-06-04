import React from 'react';

export const CardSkeleton: React.FC = () => {
  return (
    <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm animate-pulse space-y-4">
      <div className="flex justify-between items-start">
        <div className="h-6 bg-gray-200 rounded w-1/3"></div>
        <div className="h-5 bg-gray-200 rounded-full w-20"></div>
      </div>
      <div className="space-y-2">
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        <div className="h-4 bg-gray-200 rounded w-5/6"></div>
      </div>
      <div className="h-[1px] bg-gray-100 my-4"></div>
      <div className="flex gap-4">
        <div className="h-10 bg-gray-200 rounded w-1/4"></div>
        <div className="h-10 bg-gray-200 rounded w-1/4"></div>
        <div className="h-10 bg-gray-200 rounded w-1/4"></div>
      </div>
    </div>
  );
};

export const ListSkeleton: React.FC = () => {
  return (
    <div className="space-y-4">
      <CardSkeleton />
      <CardSkeleton />
      <CardSkeleton />
    </div>
  );
};

export const ChatBubbleSkeleton: React.FC = () => {
  return (
    <div className="flex flex-col space-y-4 p-4 animate-pulse">
      <div className="flex items-start gap-2.5">
        <div className="w-8 h-8 rounded-full bg-gray-200"></div>
        <div className="flex flex-col gap-1 w-full max-w-[320px]">
          <div className="h-16 bg-gray-200 rounded-2xl rounded-tl-none"></div>
        </div>
      </div>
      <div className="flex items-start gap-2.5 justify-end">
        <div className="flex flex-col gap-1 w-full max-w-[320px]">
          <div className="h-10 bg-gray-200 rounded-2xl rounded-tr-none"></div>
        </div>
        <div className="w-8 h-8 rounded-full bg-gray-200"></div>
      </div>
      <div className="flex items-start gap-2.5">
        <div className="w-8 h-8 rounded-full bg-gray-200"></div>
        <div className="flex flex-col gap-2 w-full max-w-[320px]">
          <div className="h-12 bg-gray-200 rounded-2xl rounded-tl-none"></div>
          <div className="flex gap-2">
            <div className="h-8 bg-gray-200 rounded-lg w-20"></div>
            <div className="h-8 bg-gray-200 rounded-lg w-24"></div>
          </div>
        </div>
      </div>
    </div>
  );
};
