import React from "react";

export const LoadingIndicator: React.FC = () => {
  return (
    <div className="flex justify-start">
      <div className="flex gap-1 sm:gap-2 md:gap-3">
        <div className="w-6 h-6 md:w-8 md:h-8 rounded-full bg-gradient-to-r from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-600 flex items-center justify-center flex-shrink-0">
          <span className="text-slate-600 dark:text-slate-300 text-[10px] md:text-xs font-semibold">
            AI
          </span>
        </div>
        <div className="flex items-center space-x-1 bg-slate-50 dark:bg-slate-800/50 rounded-2xl rounded-bl-md px-2 sm:px-4 py-3">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
            <div
              className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
              style={{ animationDelay: "0.1s" }}
            ></div>
            <div
              className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
              style={{ animationDelay: "0.2s" }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  );
};
