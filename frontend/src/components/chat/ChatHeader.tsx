import React from "react";

interface ChatHeaderProps {
  sessionId: string | null;
  dark: boolean;
  setDark: (dark: boolean) => void;
  onNewChat: () => void;
  hasMessages: boolean;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  sessionId,
  dark,
  setDark,
  onNewChat,
  hasMessages,
}) => {
  return (
    <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200/60 dark:border-slate-700/60 bg-gradient-to-r from-slate-50 to-white dark:from-slate-800 dark:to-slate-900">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-teal-500 flex items-center justify-center">
          <span className="text-white text-sm font-semibold">AI</span>
        </div>
        <div>
          <h3 className="font-semibold text-slate-800 dark:text-slate-100">
            AI Assistant
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Ready to help
          </p>
        </div>
      </div>

      {/* Center brand information */}
      <div className="hidden md:flex flex-col items-center text-center">
        <h1 className="text-lg font-bold tracking-tight text-slate-800 dark:text-slate-100">
          Multimodal Chatbot
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Unified text, vision & data analysis assistant
        </p>
      </div>

      <div className="flex items-center gap-2">
        {hasMessages && (
          <button
            onClick={onNewChat}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-lg text-sm font-medium transition-colors"
            aria-label="Start new chat"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            New Chat
          </button>
        )}
        <button
          onClick={() => setDark(!dark)}
          className="w-8 h-8 rounded-lg flex items-center justify-center bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
          aria-label="Toggle dark mode"
        >
          {dark ? (
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
              />
            </svg>
          ) : (
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
              />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
};
