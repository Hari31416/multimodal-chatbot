import React, { useState } from "react";
import { ChatMessage as ChatMessageType } from "../../types/chat";
import { MarkdownRenderer } from "./MarkdownRenderer";

interface ChatMessageProps {
  message: ChatMessageType;
  isLast: boolean;
  pending: boolean;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  isLast,
  pending,
}) => {
  const isUser = message.role === "user";
  const [showImage, setShowImage] = useState(false);

  const overlay =
    showImage && message.imageUrl ? (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/80 p-4 backdrop-blur-sm"
        role="dialog"
        aria-modal="true"
        onClick={() => setShowImage(false)}
      >
        <div
          className="relative max-w-5xl w-full"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() => setShowImage(false)}
            className="absolute -top-10 right-0 text-slate-200 hover:text-white p-2"
            aria-label="Close image"
          >
            <svg
              className="w-6 h-6"
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
          <img
            src={message.imageUrl}
            alt="Full size"
            className="w-full h-auto max-h-[80vh] object-contain rounded-xl shadow-2xl"
          />
        </div>
      </div>
    ) : null;

  if (isUser) {
    return (
      <>
        <div className="flex justify-end">
          <div className="max-w-2xl space-y-2">
            <div className="flex flex-col items-end gap-3">
              {message.imageUrl && (
                <button
                  type="button"
                  onClick={() => setShowImage(true)}
                  className="rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-700 shadow-sm w-64 h-64 bg-slate-50 dark:bg-slate-800 group relative focus:outline-none focus:ring-2 focus:ring-teal-500"
                  aria-label="View full image"
                >
                  <img
                    src={message.imageUrl}
                    alt="User upload"
                    className="object-cover w-full h-full transition-transform duration-200 group-hover:scale-105"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-slate-900/0 group-hover:bg-slate-900/20 flex items-center justify-center text-white text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                    Click to enlarge
                  </div>
                </button>
              )}
              <div className="bg-gradient-to-r from-blue-500 to-teal-500 text-white rounded-2xl rounded-br-md px-4 py-3 shadow-lg">
                <p className="text-sm whitespace-pre-wrap break-words">
                  {message.content}
                </p>
              </div>
            </div>
            <div className="flex justify-end mt-1">
              <span className="text-xs text-slate-400">You</span>
            </div>
          </div>
        </div>
        {overlay}
      </>
    );
  }

  return (
    <>
      <div className="flex justify-start">
        <div className="max-w-3xl w-full">
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-600 flex items-center justify-center flex-shrink-0 mt-1">
              <span className="text-slate-600 dark:text-slate-300 text-xs font-semibold">
                AI
              </span>
            </div>
            <div className="flex-1 space-y-3">
              <MarkdownRenderer content={message.content} />
              <div className="flex gap-2 items-center flex-wrap px-1">
                {message.modality === "data" && (
                  <span className="text-[10px] uppercase tracking-wide font-semibold px-2 py-1 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300">
                    📊 Data
                  </span>
                )}
                {pending && isLast && (
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <div className="flex space-x-1">
                      <div className="w-1 h-1 bg-slate-400 rounded-full animate-bounce" />
                      <div
                        className="w-1 h-1 bg-slate-400 rounded-full animate-bounce"
                        style={{ animationDelay: "0.1s" }}
                      />
                      <div
                        className="w-1 h-1 bg-slate-400 rounded-full animate-bounce"
                        style={{ animationDelay: "0.2s" }}
                      />
                    </div>
                    Thinking
                  </span>
                )}
              </div>
              {message.artifacts && (
                <div className="space-y-3 px-1">
                  {message.artifacts.chart && (
                    <div className="rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm bg-white dark:bg-slate-800/50">
                      <img
                        src={message.artifacts.chart}
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
      {overlay}
    </>
  );
};
