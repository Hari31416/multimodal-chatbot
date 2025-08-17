import React, { useState, useEffect, useRef } from "react";
import { getJSON, postForm } from "../../api/client";

interface SessionInfo {
  session_id: string;
  created_at: number;
  last_accessed: number;
  title?: string;
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
  const loadedOnceRef = useRef(false);
  // Cache reference for session list + timestamp
  const sessionsCacheRef = useRef<{
    data: SessionInfo[];
    fetchedAt: number;
  } | null>(null);
  const SESSIONS_TTL_MS = 60_000; // 1 minute TTL (adjust as needed)

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
        sessionIds: string[];
        titles: string[];
      }>("/all-sessions");

      const sessionInfos: SessionInfo[] = response.sessionIds.map(
        (id, index) => ({
          session_id: id,
          created_at: Date.now(),
          last_accessed: Date.now(),
          title: response.titles[index] || "Chat Session",
        })
      );

      sessionsCacheRef.current = { data: sessionInfos, fetchedAt: now };
      setSessions(sessionInfos);
    } catch (err: any) {
      setError("Failed to load sessions: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadSessionHistory = async (sessionId: string) => {
    try {
      const formData = new FormData();
      formData.append("sessionId", sessionId);

      const response = await postForm<SessionHistory>(
        "/all-previous-chats",
        formData
      );
      onSessionSelect(sessionId, response.messages);
    } catch (err: any) {
      setError("Failed to load session history: " + err.message);
    }
  };

  const handleDeleteSession = async (
    sessionId: string,
    e: React.MouseEvent<HTMLButtonElement>
  ) => {
    e.stopPropagation();
    if (deleting) return; // prevent concurrent
    const confirmDelete = window.confirm("Delete this chat session?");
    if (!confirmDelete) return;
    setDeleting(sessionId);
    setError("");
    try {
      const formData = new FormData();
      formData.append("sessionId", sessionId);
      await postForm("/delete-session", formData);

      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
      // Update cache
      if (sessionsCacheRef.current) {
        sessionsCacheRef.current = {
          ...sessionsCacheRef.current,
          data: sessionsCacheRef.current.data.filter(
            (s) => s.session_id !== sessionId
          ),
        };
      }
      // If current session deleted, optionally start a fresh one
      if (currentSessionId === sessionId) {
        try {
          await onNewChat();
        } catch {}
      }
    } catch (err: any) {
      setError("Failed to delete session: " + err.message);
    } finally {
      setDeleting(null);
    }
  };

  const formatDate = (timestamp: number) => {
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
                    key={session.session_id}
                    onClick={() => {
                      loadSessionHistory(session.session_id);
                      onToggle();
                    }}
                    className={`relative group w-full text-left p-3 rounded-md transition-colors duration-200 ${
                      currentSessionId === session.session_id
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
                          {formatDate(session.last_accessed)}
                        </span>
                      </div>
                    </div>
                    <button
                      type="button"
                      aria-label="Delete session"
                      title="Delete session"
                      onClick={(e) =>
                        handleDeleteSession(session.session_id, e)
                      }
                      disabled={deleting === session.session_id}
                      className={`absolute top-2 right-2 p-1 rounded-md text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 dark:hover:text-red-400 focus:outline-none focus:ring-2 focus:ring-red-500 transition-opacity ${
                        deleting === session.session_id
                          ? "opacity-100"
                          : "opacity-0 group-hover:opacity-100"
                      }`}
                    >
                      {deleting === session.session_id ? (
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
        </div>
      </div>
    </>
  );
};

export default Sidebar;
