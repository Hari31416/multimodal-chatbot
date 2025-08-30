import React, { useState, useEffect, useRef } from "react";
import { getJSON, deleteJSON } from "../../api/client";

interface SessionInfo {
  sessionId: string;
  userId: string;
  createdAt: string;
  updatedAt: string;
  title: string;
  numMessages: number;
  numArtifacts: number;
}

interface ChatMessage {
  role: string;
  content: string | any[]; // may be multimodal list from backend
}

interface SessionHistory {
  sessionId: string;
  messages: ChatMessage[];
}

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  currentSessionId: string | null;
  onSessionSelect: (sessionId: string, messages: ChatMessage[]) => void;
  onNewChat: () => void;
  dark: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onToggle,
  currentSessionId,
  onSessionSelect,
  onNewChat,
  dark,
}) => {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [deleting, setDeleting] = useState<string | null>(null);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const loadedOnceRef = useRef(false);
  // Cache reference for session list + timestamp
  const sessionsCacheRef = useRef<{
    data: SessionInfo[];
    fetchedAt: number;
  } | null>(null);
  const SESSIONS_TTL_MS = 60_000; // 1 minute TTL (adjust as needed)

  const sidebarRef = useRef<HTMLDivElement | null>(null);

  // Prefetch sessions on first mount
  useEffect(() => {
    if (!loadedOnceRef.current) {
      loadedOnceRef.current = true;
      loadSessions();
    }
  }, []);

  // Also refresh whenever sidebar is opened explicitly
  useEffect(() => {
    if (isOpen) {
      loadSessions();
    }
  }, [isOpen]);

  // Close on outside click (desktop). Mobile already uses overlay.
  useEffect(() => {
    if (!isOpen) return;
    function handleClick(e: MouseEvent) {
      if (
        sidebarRef.current &&
        !sidebarRef.current.contains(e.target as Node)
      ) {
        onToggle();
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [isOpen, onToggle]);

  const loadSessions = async (opts: { force?: boolean } = {}) => {
    const { force = false } = opts;
    const now = Date.now();
    // Serve from cache if not forcing and cache valid
    if (!force && sessionsCacheRef.current) {
      const age = now - sessionsCacheRef.current.fetchedAt;
      if (age < SESSIONS_TTL_MS && sessionsCacheRef.current.data.length) {
        setSessions(sessionsCacheRef.current.data);
        return; // cache hit
      }
    }
    setLoading(true);
    setError("");
    try {
      const response = await getJSON<{
        sessions: SessionInfo[];
      }>("/sessions/list?user_id=default_user");

      sessionsCacheRef.current = { data: response.sessions, fetchedAt: now };
      setSessions(response.sessions);
    } catch (err: any) {
      setError("Failed to load sessions: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadSessionHistory = async (sessionId: string) => {
    try {
      const response = await getJSON<{
        sessionId: string;
        userId: string;
        createdAt: string;
        updatedAt: string;
        title: string;
        numMessages: number;
        numArtifacts: number;
        messages: ChatMessage[];
      }>(`/sessions/${sessionId}?user_id=default_user`);

      onSessionSelect(sessionId, response.messages);
    } catch (err: any) {
      setError("Failed to load session history: " + err.message);
    }
  };
  const handleDeleteSession = async (sessionId: string) => {
    if (deleting) return;
    setDeleting(sessionId);
    setError("");
    try {
      await deleteJSON(`/sessions/delete/${sessionId}?user_id=default_user`);
      setSessions((prev) => prev.filter((s) => s.sessionId !== sessionId));
      if (sessionsCacheRef.current) {
        sessionsCacheRef.current = {
          ...sessionsCacheRef.current,
          data: sessionsCacheRef.current.data.filter(
            (s) => s.sessionId !== sessionId
          ),
        };
      }
      if (currentSessionId === sessionId) {
        try {
          await onNewChat();
        } catch {}
      }
    } catch (err: any) {
      setError("Failed to delete session: " + err.message);
    } finally {
      setDeleting(null);
      setConfirmingId(null);
    }
  };

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
    } else if (diffDays === 1) {
      return "Yesterday";
    } else if (diffDays < 7) {
      return date.toLocaleDateString([], { weekday: "short" });
    } else {
      return date.toLocaleDateString([], { month: "short", day: "numeric" });
    }
  };

  const truncateTitle = (title: string, maxLength: number = 30) => {
    return title.length > maxLength
      ? title.substring(0, maxLength) + "..."
      : title;
  };

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed lg:fixed left-0 top-0 h-full w-80 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 transform transition-transform duration-300 ease-in-out z-50 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        aria-hidden={!isOpen}
        ref={sidebarRef}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-4 border-b border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                Chat History
              </h2>
              <button
                onClick={onToggle}
                aria-label="Close sidebar"
                className="p-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-700"
              >
                <svg
                  className="w-5 h-5 text-slate-600 dark:text-slate-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            {/* New Chat Button */}
            <button
              onClick={async () => {
                await onNewChat();
                // Force refresh to include the brand new session
                loadSessions({ force: true });
                onToggle(); // Close sidebar (mobile)
              }}
              className="w-full mt-3 px-3 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md transition-colors duration-200"
            >
              + New Chat
            </button>
          </div>

          {/* Sessions List */}
          <div className="flex-1 overflow-y-auto">
            {loading && (
              <div className="p-4 text-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mx-auto"></div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
                  Loading sessions...
                </p>
              </div>
            )}

            {error && (
              <div className="p-4">
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-3">
                  <p className="text-sm text-red-700 dark:text-red-400">
                    {error}
                  </p>
                </div>
              </div>
            )}

            {!loading && !error && sessions.length === 0 && (
              <div className="p-4 text-center">
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  No previous chats found
                </p>
              </div>
            )}

            {!loading && !error && sessions.length > 0 && (
              <div className="p-2 space-y-1">
                {sessions.map((session) => (
                  <button
                    key={session.sessionId}
                    onClick={() => {
                      loadSessionHistory(session.sessionId);
                      onToggle();
                    }}
                    className={`relative group w-full text-left p-3 rounded-md transition-colors duration-200 ${
                      currentSessionId === session.sessionId
                        ? "bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800"
                        : "hover:bg-slate-50 dark:hover:bg-slate-700"
                    }`}
                  >
                    <div className="flex flex-col pr-6">
                      {/* space for delete btn */}
                      <h3 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-1">
                        {truncateTitle(session.title || "Chat Session")}
                      </h3>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-500 dark:text-slate-400">
                          {formatDate(session.updatedAt)}
                        </span>
                        <span className="text-xs text-slate-400 dark:text-slate-500">
                          {session.numMessages} messages
                        </span>
                      </div>
                    </div>
                    <button
                      type="button"
                      aria-label="Delete session"
                      title="Delete session"
                      onClick={(e) => {
                        e.stopPropagation();
                        setConfirmingId(session.sessionId);
                      }}
                      disabled={deleting === session.sessionId}
                      className={`absolute top-2 right-2 p-1 rounded-md text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 dark:hover:text-red-400 focus:outline-none focus:ring-2 focus:ring-red-500 transition-opacity ${
                        deleting === session.sessionId
                          ? "opacity-100"
                          : "opacity-0 group-hover:opacity-100"
                      }`}
                    >
                      {deleting === session.sessionId ? (
                        <svg
                          className="w-4 h-4 animate-spin"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            strokeWidth="4"
                          ></circle>
                          <path
                            className="opacity-75"
                            d="M4 12a8 8 0 018-8"
                            strokeWidth="4"
                            strokeLinecap="round"
                          ></path>
                        </svg>
                      ) : (
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth={2}
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M9 7h6m2 0H7m3-3h4a1 1 0 011 1v2H9V5a1 1 0 011-1z"
                          />
                        </svg>
                      )}
                    </button>
                  </button>
                ))}
              </div>
            )}
          </div>
          {confirmingId && (
            <div
              className="absolute inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
              role="dialog"
              aria-modal="true"
            >
              <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl w-full max-w-sm border border-slate-200 dark:border-slate-700">
                <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center gap-2">
                  <svg
                    className="w-5 h-5 text-red-500"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 9v4m0 4h.01M4.93 4.93l14.14 14.14M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                    Delete Chat
                  </h3>
                </div>
                <div className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300 space-y-3">
                  <p>
                    Are you sure you want to delete this chat session? This
                    action cannot be undone.
                  </p>
                </div>
                <div className="px-5 py-3 flex items-center justify-end gap-2 bg-slate-50 dark:bg-slate-700/30 rounded-b-lg">
                  <button
                    onClick={() => setConfirmingId(null)}
                    className="px-3 py-1.5 rounded-md text-sm font-medium bg-white dark:bg-slate-600 border border-slate-300 dark:border-slate-500 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-500"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => handleDeleteSession(confirmingId)}
                    className="px-3 py-1.5 rounded-md text-sm font-medium bg-red-600 hover:bg-red-700 text-white shadow-sm disabled:opacity-60"
                    disabled={deleting === confirmingId}
                  >
                    {deleting === confirmingId ? "Deleting…" : "Delete"}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default Sidebar;
