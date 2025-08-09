import React from "react";
import { ChatMessage as ChatMessageType } from "../../types/chat";

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

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-2xl">
          <div className="bg-gradient-to-r from-blue-500 to-teal-500 text-white rounded-2xl rounded-br-md px-4 py-3 shadow-lg">
            <p className="text-sm">{message.content}</p>
          </div>
          <div className="flex justify-end mt-1">
            <span className="text-xs text-slate-400">You</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
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
                {message.content}
              </div>
            </div>
            <div className="flex gap-2 items-center flex-wrap px-1">
              {message.modality !== "text" && (
                <span
                  className={`text-[10px] uppercase tracking-wide font-semibold px-2 py-1 rounded-full ${
                    message.modality === "vision"
                      ? "bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300"
                      : message.modality === "data"
                      ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300"
                      : "bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                  }`}
                >
                  {message.modality === "vision"
                    ? "🖼️ Vision"
                    : message.modality === "data"
                    ? "📊 Data"
                    : message.modality}
                </span>
              )}
              {pending && isLast && (
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
  );
};
