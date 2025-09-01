import React from "react";

interface ChatHeaderProps {
  sessionId: string | null;
  dark: boolean;
  setDark: (dark: boolean) => void;
  // onNewChat: () => void; // Removed New Chat button logic
  hasMessages: boolean;
  onShowDataset: () => void;
  datasetAvailable?: boolean;
  onToggleSidebar?: () => void;
  sidebarOpen?: boolean;
  onNewChat?: () => void; // New chat trigger when sidebar collapsed
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  sessionId,
  dark,
  setDark,
  // onNewChat, // Removed New Chat button logic
  hasMessages,
  onShowDataset,
  datasetAvailable = false,
  onToggleSidebar,
  sidebarOpen = false,
  onNewChat,
}) => {
  return (
    <header className="border-b border-slate-200/60 dark:border-slate-700/60 bg-gradient-to-r from-slate-50 to-white dark:from-slate-800 dark:to-slate-900 px-2 sm:px-4 md:px-6 py-3 flex flex-col gap-2">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          {onToggleSidebar && (
            <button
              onClick={onToggleSidebar}
              className="w-9 h-9 rounded-lg flex items-center justify-center bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
              aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
            >
              {sidebarOpen ? (
                // Collapse (chevron-left within panel shape)
                <svg
                  className="w-5 h-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M4 5a2 2 0 012-2h8a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V5z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M11 8l-3 4 3 4"
                  />
                </svg>
              ) : (
                // Open (hamburger menu)
                <svg
                  className="w-5 h-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M4 6h16M4 12h16M4 18h10"
                  />
                </svg>
              )}
            </button>
          )}
          {/* When sidebar is closed, show quick new-chat + button (desktop & mobile) */}
          {!sidebarOpen && onNewChat && (
            <button
              onClick={onNewChat}
              aria-label="Start new chat"
              className="w-9 h-9 rounded-lg flex items-center justify-center bg-indigo-500 hover:bg-indigo-600 text-white transition-colors shadow-sm"
            >
              <svg
                className="w-5 h-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 5v14M5 12h14"
                />
              </svg>
            </button>
          )}
        </div>
        <div className="hidden md:flex flex-col items-center justify-center text-center px-2">
          <h1 className="text-base md:text-lg font-bold tracking-tight text-slate-800 dark:text-slate-100">
            Advanced Chatbot
          </h1>
        </div>
        <div className="flex items-center gap-2">
          {datasetAvailable && (
            <button
              onClick={onShowDataset}
              className="flex items-center gap-1 px-3 py-1.5 bg-emerald-500/90 hover:bg-emerald-600 text-white rounded-lg text-xs font-medium transition-colors shadow-sm"
              aria-label="Show dataset overview"
            >
              <span className="text-xs">📊</span>
              <span className="hidden sm:inline">Dataset</span>
            </button>
          )}
          <button
            onClick={() => setDark(!dark)}
            className="w-9 h-9 rounded-lg flex items-center justify-center bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
            aria-label="Toggle dark mode"
          >
            {dark ? (
              <svg
                className="w-5 h-5"
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
                className="w-5 h-5"
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
    </header>
  );
};
