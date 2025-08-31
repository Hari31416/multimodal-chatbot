import React, { useState } from "react";
import { ChatMessage as ChatMessageType } from "../../types/chat";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { DataArtifactViewer } from "./DataArtifactViewer";
import { AnalysisCodeBlock } from "./AnalysisCodeBlock";
import { LazyDataImage } from "./LazyDataImage";

interface ChatMessageProps {
  message: ChatMessageType;
  isLast: boolean;
  pending: boolean;
  onRetry?: (message: ChatMessageType) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  isLast,
  pending,
  onRetry,
}) => {
  const isUser = message.role === "user";
  const [showImage, setShowImage] = useState(false);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  const handleRetry = () => {
    if (onRetry) {
      onRetry(message);
    }
  };

  // Get images to display - prefer imageUrls array, fallback to single imageUrl
  const imagesToDisplay =
    message.imageUrls && message.imageUrls.length > 0
      ? message.imageUrls
      : message.imageUrl
      ? [message.imageUrl]
      : [];

  const overlay =
    showImage && imagesToDisplay.length > 0 ? (
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
          {imagesToDisplay.length > 1 && (
            <div className="absolute -top-10 left-0 text-slate-200 text-sm">
              {selectedImageIndex + 1} / {imagesToDisplay.length}
            </div>
          )}
          {imagesToDisplay.length > 1 && (
            <>
              <button
                onClick={() =>
                  setSelectedImageIndex(Math.max(0, selectedImageIndex - 1))
                }
                className="absolute left-4 top-1/2 transform -translate-y-1/2 text-slate-200 hover:text-white p-2 disabled:opacity-50"
                disabled={selectedImageIndex === 0}
                aria-label="Previous image"
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
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </button>
              <button
                onClick={() =>
                  setSelectedImageIndex(
                    Math.min(imagesToDisplay.length - 1, selectedImageIndex + 1)
                  )
                }
                className="absolute right-4 top-1/2 transform -translate-y-1/2 text-slate-200 hover:text-white p-2 disabled:opacity-50"
                disabled={selectedImageIndex === imagesToDisplay.length - 1}
                aria-label="Next image"
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
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </button>
            </>
          )}
          <img
            src={imagesToDisplay[selectedImageIndex]}
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
              {imagesToDisplay.length > 0 && (
                <div className="flex flex-wrap gap-2 justify-end">
                  {imagesToDisplay.map((imageUrl, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => {
                        setSelectedImageIndex(index);
                        setShowImage(true);
                      }}
                      className="rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-700 shadow-sm w-32 h-32 bg-slate-50 dark:bg-slate-800 group relative focus:outline-none focus:ring-2 focus:ring-teal-500"
                      aria-label={`View image ${index + 1}`}
                    >
                      <LazyDataImage
                        dataUrl={imageUrl}
                        alt={`User upload ${index + 1}`}
                        wrapperClassName="w-full h-full"
                        className="object-cover w-full h-full transition-transform duration-200 group-hover:scale-105"
                      />
                      <div className="absolute inset-0 bg-slate-900/0 group-hover:bg-slate-900/20 flex items-center justify-center text-white text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                        Click to enlarge
                      </div>
                      {imagesToDisplay.length > 1 && (
                        <div className="absolute top-1 right-1 bg-slate-900/70 text-white text-xs px-1 py-0.5 rounded">
                          {index + 1}
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              )}
              <div className="bg-gradient-to-r from-blue-500 to-teal-500 text-white rounded-2xl rounded-br-md px-4 py-3 shadow-lg">
                <p className="text-sm whitespace-pre-wrap break-words">
                  {message.content}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleCopy}
                  className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors p-1 rounded"
                  title="Copy message"
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
                      d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                    />
                  </svg>
                </button>
                <button
                  onClick={handleRetry}
                  className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors p-1 rounded"
                  title="Retry message"
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
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                </button>
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
              {message.modality === "vision" && message.imageUrl && (
                <button
                  type="button"
                  onClick={() => setShowImage(true)}
                  className="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700 shadow-sm w-56 h-56 bg-slate-50 dark:bg-slate-800 group relative focus:outline-none focus:ring-2 focus:ring-teal-500"
                  aria-label="View image"
                >
                  <LazyDataImage
                    dataUrl={message.imageUrl}
                    alt="Vision input"
                    wrapperClassName="w-full h-full"
                    className="object-cover w-full h-full transition-transform duration-200 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-slate-900/0 group-hover:bg-slate-900/20 flex items-center justify-center text-white text-[11px] font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                    Click to enlarge
                  </div>
                </button>
              )}
              <div className="markdown-output">
                <MarkdownRenderer content={message.content} />
              </div>
              <div className="flex gap-2 items-center flex-wrap px-1">
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
                {!pending && (
                  <button
                    onClick={handleCopy}
                    className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors p-1 rounded"
                    title="Copy message"
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
                        d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                      />
                    </svg>
                  </button>
                )}
              </div>
              {(message.artifact || message.code) && (
                <div className="px-1 space-y-6">
                  {message.artifact && (
                    <DataArtifactViewer
                      chart={message.artifact.chart}
                      text={message.artifact.text}
                      raw={message.artifact.raw}
                      isMime={message.artifact.isMime}
                    />
                  )}
                  {message.code && <AnalysisCodeBlock code={message.code} />}
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
