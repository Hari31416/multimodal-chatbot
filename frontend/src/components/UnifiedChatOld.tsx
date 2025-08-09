import React, { useState, useRef, useEffect } from "react";
import {
  ChatHeader,
  ChatMessage,
  ChatInput,
  EmptyState,
  DatasetOverview,
  LoadingIndicator,
} from "./chat";
import { useChatLogic } from "../hooks/useChatLogic";

interface UnifiedChatProps {
  dark: boolean;
  setDark: (dark: boolean) => void;
}

const UnifiedChat: React.FC<UnifiedChatProps> = ({ dark, setDark }) => {
  const [pickerOpen, setPickerOpen] = useState(false);
  const fileInputImageRef = useRef<HTMLInputElement | null>(null);
  const fileInputCsvRef = useRef<HTMLInputElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const {
    messages,
    input,
    setInput,
    pending,
    error,
    imageFile,
    setImageFile,
    sessionId,
    columns,
    head,
    handleNewChat,
    handleSend,
    handleCsvUpload,
  } = useChatLogic();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, pending]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        pickerRef.current &&
        !pickerRef.current.contains(event.target as Node)
      ) {
        setPickerOpen(false);
      }
    }

    if (pickerOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => {
        document.removeEventListener("mousedown", handleClickOutside);
      };
    }
  }, [pickerOpen]);
}

  return (
    <section className="h-full flex flex-col bg-white dark:bg-slate-900">
      {/* Header */}
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
              {sessionId
                ? `Data Session • ${sessionId.slice(0, 8)}...`
                : "Ready to help"}
            </p>
          </div>
        </div>
        
        {/* Center brand information */}
        <div className="hidden md:flex flex-col items-center text-center">
          <h1 className="text-lg font-bold tracking-tight text-slate-800 dark:text-slate-100">
            Multimodal Chatbot MVP
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Unified text, vision & data analysis assistant
          </p>
        </div>

        <div className="flex items-center gap-2">
          {sessionId && (
            <span className="inline-flex items-center gap-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 px-2 py-1 rounded-full text-xs font-medium">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
              Data Mode
            </span>
          )}
          {messages.length > 0 && (
            <button
              onClick={handleNewChat}
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
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Messages Container */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-6 py-6 space-y-6 text-[15px] leading-relaxed"
      >
        {messages.length === 0 && !pending && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-6">
            <div className="w-16 h-16 rounded-full bg-gradient-to-r from-blue-500 to-teal-500 flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            </div>
            <div className="max-w-md space-y-2">
              <h4 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
                Welcome to AI Assistant
              </h4>
              <p className="text-slate-500 dark:text-slate-400 text-sm">
                I can help you with conversations, analyze images, and process
                CSV data. What would you like to explore today?
              </p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center">
              <span className="px-3 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-full text-xs font-medium">
                💬 Chat
              </span>
              <span className="px-3 py-1 bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-300 rounded-full text-xs font-medium">
                🖼️ Vision
              </span>
              <span className="px-3 py-1 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 rounded-full text-xs font-medium">
                📊 Data Analysis
              </span>
            </div>
          </div>
        )}
        {messages.map((m) => {
          const isUser = m.role === "user";
          if (isUser) {
            return (
              <div key={m.id} className="flex justify-end">
                <div className="max-w-2xl">
                  <div className="bg-gradient-to-r from-blue-500 to-teal-500 text-white rounded-2xl rounded-br-md px-4 py-3 shadow-lg">
                    <p className="text-sm">{m.content}</p>
                  </div>
                  <div className="flex justify-end mt-1">
                    <span className="text-xs text-slate-400">You</span>
                  </div>
                </div>
              </div>
            );
          }
          return (
            <div key={m.id} className="flex justify-start">
              <div className="max-w-3xl w-full">
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-600 flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-slate-600 dark:text-slate-300 text-xs font-semibold">
                      AI
                    </span>
                  </div>
                  <div className="flex-1 space-y-3">
                    <div className="bg-slate-50 dark:bg-slate-800/50 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm border border-slate-200/60 dark:border-slate-700/60">
                      <div className="text-slate-800 dark:text-slate-100 whitespace-pre-wrap break-words">
                        {m.content}
                      </div>
                    </div>
                    <div className="flex gap-2 items-center flex-wrap px-1">
                      {m.modality !== "text" && (
                        <span
                          className={`text-[10px] uppercase tracking-wide font-semibold px-2 py-1 rounded-full ${
                            m.modality === "vision"
                              ? "bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300"
                              : m.modality === "data"
                              ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300"
                              : "bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                          }`}
                        >
                          {m.modality === "vision"
                            ? "🖼️ Vision"
                            : m.modality === "data"
                            ? "📊 Data"
                            : m.modality}
                        </span>
                      )}
                      {pending && m === messages[messages.length - 1] && (
                        <span className="text-xs text-slate-400 flex items-center gap-1">
                          <div className="flex space-x-1">
                            <div className="w-1 h-1 bg-slate-400 rounded-full animate-bounce"></div>
                            <div
                              className="w-1 h-1 bg-slate-400 rounded-full animate-bounce"
                              style={{ animationDelay: "0.1s" }}
                            ></div>
                            <div
                              className="w-1 h-1 bg-slate-400 rounded-full animate-bounce"
                              style={{ animationDelay: "0.2s" }}
                            ></div>
                          </div>
                          Thinking
                        </span>
                      )}
                    </div>
                    {m.artifacts && (
                      <div className="space-y-3 px-1">
                        {m.artifacts.chart && (
                          <div className="rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm bg-white dark:bg-slate-800/50">
                            <img
                              src={m.artifacts.chart}
                              alt="Chart"
                              className="w-full max-h-80 object-contain"
                            />
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
        {pending && messages.length > 0 && (
          <div className="flex justify-start">
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-600 flex items-center justify-center flex-shrink-0">
                <span className="text-slate-600 dark:text-slate-300 text-xs font-semibold">
                  AI
                </span>
              </div>
              <div className="flex items-center space-x-1 bg-slate-50 dark:bg-slate-800/50 rounded-2xl rounded-bl-md px-4 py-3">
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
        )}
      </div>
      {/* Bottom input bar */}
      <div className="border-t border-slate-200/60 dark:border-slate-700/60 bg-white dark:bg-slate-900 px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <div className="relative">
            {/* Attachment indicators */}
            <div className="flex gap-2 mb-3">
              {imageFile && (
                <div className="flex items-center gap-2 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-700/50 rounded-xl px-3 py-2 text-sm">
                  <div className="w-5 h-5 rounded bg-orange-100 dark:bg-orange-800 flex items-center justify-center">
                    <span className="text-xs">🖼️</span>
                  </div>
                  <span className="font-medium text-orange-700 dark:text-orange-300">
                    Image:
                  </span>
                  <span className="max-w-[140px] truncate text-orange-600 dark:text-orange-400">
                    {imageFile.name}
                  </span>
                  <button
                    onClick={() => {
                      setImageFile(null);
                      if (fileInputImageRef.current)
                        fileInputImageRef.current.value = "";
                    }}
                    className="text-orange-500 hover:text-orange-700 dark:hover:text-orange-300 transition-colors"
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
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>
              )}
            </div>

            {/* Input container */}
            <div className="relative flex items-end gap-3 rounded-2xl border border-slate-300/60 dark:border-slate-600/60 bg-white dark:bg-slate-800 shadow-lg hover:shadow-xl transition-shadow duration-200 overflow-hidden">
              {/* Attachment button */}
              <div className="relative p-3" ref={pickerRef}>
                <button
                  ref={attachmentButtonRef}
                  type="button"
                  onClick={() => setPickerOpen((o) => !o)}
                  className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${
                    pickerOpen
                      ? "bg-teal-500 text-white shadow-lg"
                      : "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600"
                  }`}
                  aria-label="Add attachment"
                >
                  <svg
                    className={`w-5 h-5 transition-transform duration-200 ${
                      pickerOpen ? "rotate-45" : ""
                    }`}
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
                </button>

                {/* Attachment picker */}
                {pickerOpen &&
                  attachmentButtonRef.current &&
                  createPortal(
                    <div
                      ref={pickerRef}
                      className="fixed w-52 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-2xl z-[9999] overflow-hidden"
                      style={{
                        bottom:
                          window.innerHeight -
                          attachmentButtonRef.current.getBoundingClientRect()
                            .top +
                          8,
                        left: attachmentButtonRef.current.getBoundingClientRect()
                          .left,
                      }}
                    >
                      <div className="py-2">
                        <button
                          className="flex items-center w-full text-left px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors group"
                          onClick={() => {
                            setPickerOpen(false);
                            fileInputImageRef.current?.click();
                          }}
                        >
                          <div className="w-8 h-8 rounded-lg bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center mr-3 group-hover:scale-110 transition-transform">
                            <span className="text-sm">🖼️</span>
                          </div>
                          <div>
                            <p className="font-medium text-slate-800 dark:text-slate-100 text-sm">
                              Upload Image
                            </p>
                            <p className="text-xs text-slate-500 dark:text-slate-400">
                              Vision analysis
                            </p>
                          </div>
                        </button>
                        <button
                          className="flex items-center w-full text-left px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors group"
                          onClick={() => {
                            setPickerOpen(false);
                            fileInputCsvRef.current?.click();
                          }}
                        >
                          <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center mr-3 group-hover:scale-110 transition-transform">
                            <span className="text-sm">📊</span>
                          </div>
                          <div>
                            <p className="font-medium text-slate-800 dark:text-slate-100 text-sm">
                              Upload CSV
                            </p>
                            <p className="text-xs text-slate-500 dark:text-slate-400">
                              Data analysis
                            </p>
                          </div>
                        </button>
                      </div>
                      {sessionId && (
                        <div className="border-t border-slate-200 dark:border-slate-700 px-4 py-2 bg-slate-50 dark:bg-slate-700/30">
                          <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-2">
                            <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
                            Active session {sessionId.slice(0, 8)}...
                          </p>
                        </div>
                      )}
                    </div>,
                    document.body
                  )}
              </div>

              {/* Text input */}
              <div className="flex-1 py-3 pr-3">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      if (!pending && input.trim()) handleSend();
                    }
                  }}
                  placeholder={
                    imageFile
                      ? "Describe what you see in the image..."
                      : sessionId
                      ? "Ask questions about your data..."
                      : "Type your message here..."
                  }
                  rows={1}
                  className="w-full resize-none bg-transparent focus:outline-none text-sm leading-relaxed placeholder:text-slate-400 dark:placeholder:text-slate-500 max-h-32 min-h-[1.5rem]"
                  style={{
                    height: "auto",
                    minHeight: "1.5rem",
                  }}
                  onInput={(e) => {
                    const target = e.target as HTMLTextAreaElement;
                    target.style.height = "auto";
                    target.style.height = target.scrollHeight + "px";
                  }}
                />
              </div>

              {/* Send button */}
              <div className="p-3">
                <button
                  onClick={handleSend}
                  disabled={pending || !input.trim()}
                  className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 shadow-md ${
                    pending || !input.trim()
                      ? "bg-slate-200 dark:bg-slate-700 text-slate-400 dark:text-slate-500 cursor-not-allowed"
                      : "bg-gradient-to-r from-blue-500 to-teal-500 hover:from-blue-600 hover:to-teal-600 text-white shadow-lg hover:shadow-xl transform hover:scale-105"
                  }`}
                  aria-label="Send message"
                >
                  {pending ? (
                    <div className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin"></div>
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
                        d="M17 8l4 4m0 0l-4 4m4-4H3"
                      />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {/* Error display */}
            {error && (
              <div
                className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
                role="alert"
              >
                <div className="flex items-center gap-2">
                  <svg
                    className="w-4 h-4 text-red-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                    />
                  </svg>
                  <span className="text-sm text-red-700 dark:text-red-300">
                    {error}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Data preview section */}
          {columns.length > 0 && (
            <div className="mt-4 border border-slate-200 dark:border-slate-700 rounded-xl bg-white dark:bg-slate-800 shadow-sm overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-700/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                      <span className="text-xs">📊</span>
                    </div>
                    <h4 className="font-semibold text-slate-800 dark:text-slate-100 text-sm">
                      Dataset Overview
                    </h4>
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      ({columns.length} columns)
                    </span>
                  </div>
                  <button
                    onClick={() => setShowDatasetOverview(!showDatasetOverview)}
                    className="p-1 rounded hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                    aria-label={showDatasetOverview ? "Hide dataset overview" : "Show dataset overview"}
                  >
                    <svg 
                      className={`w-4 h-4 text-slate-500 dark:text-slate-400 transition-transform ${showDatasetOverview ? 'rotate-180' : ''}`} 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                </div>
              </div>
              {showDatasetOverview && (
                <div className="flex flex-wrap gap-1">
                  <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
                    Columns:
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {columns.map((col, i) => (
                      <span
                        key={i}
                        className="inline-block bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 px-2 py-0.5 rounded text-xs"
                      >
                        {col}
                      </span>
                    ))}
                  </div>
                </div>
                {head.length > 0 && (
                  <details className="group">
                    <summary className="cursor-pointer text-sm font-medium text-teal-600 dark:text-teal-400 hover:text-teal-700 dark:hover:text-teal-300 flex items-center gap-1">
                      <svg
                        className="w-4 h-4 transition-transform group-open:rotate-90"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 5l7 7-7 7"
                        />
                      </svg>
                      Preview Data ({head.length} rows)
                    </summary>
                    <div className="mt-3 overflow-x-auto border border-slate-200 dark:border-slate-700 rounded-lg">
                      <table className="w-full text-xs">
                        <tbody>
                          {head.map((row, i) => (
                            <tr
                              key={i}
                              className={`${
                                i % 2 === 0
                                  ? "bg-slate-50 dark:bg-slate-800/30"
                                  : "bg-white dark:bg-slate-800/10"
                              } hover:bg-slate-100 dark:hover:bg-slate-700/30 transition-colors`}
                            >
                              {row.map((cell, j) => (
                                <td
                                  key={j}
                                  className="px-3 py-2 border-r border-slate-200 dark:border-slate-700 last:border-r-0 whitespace-nowrap font-mono text-slate-700 dark:text-slate-300"
                                >
                                  {String(cell)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </details>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
      {/* Hidden file inputs */}
      <input
        ref={fileInputImageRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0] || null;
          setImageFile(f);
        }}
      />
      <input
        ref={fileInputCsvRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) {
            setCsvFile(f);
            handleCsvUpload(f);
          }
        }}
      />
    </section>
  );
};

export default UnifiedChat;
