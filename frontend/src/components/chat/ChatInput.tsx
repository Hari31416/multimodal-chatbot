import React, { useRef, useState } from "react";
import { AttachmentPicker } from "./AttachmentPicker";

interface ChatInputProps {
  input: string;
  setInput: (input: string) => void;
  pending: boolean;
  sessionId: string | null;
  pickerOpen: boolean;
  setPickerOpen: (open: boolean) => void;
  onSend: () => void;
  error: string;
  fileInputImageRef: React.RefObject<HTMLInputElement>;
  fileInputCsvRef: React.RefObject<HTMLInputElement>;
  onImageUpload: (files: File[]) => void;
  hasUploadedImages?: boolean;
  hasUploadedData?: boolean;
  uploadedImageArtifacts?: Array<{
    artifactId: string;
    data: string;
    fileName: string;
    description: string;
  }>;
  onRemoveImageArtifact?: (artifactId: string) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  input,
  setInput,
  pending,
  sessionId,
  pickerOpen,
  setPickerOpen,
  onSend,
  error,
  fileInputImageRef,
  fileInputCsvRef,
  onImageUpload,
  hasUploadedImages = false,
  hasUploadedData = false,
  uploadedImageArtifacts = [],
  onRemoveImageArtifact,
}) => {
  const attachmentButtonRef = useRef<HTMLButtonElement | null>(null);
  const [focused, setFocused] = useState(false);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!pending && input.trim()) onSend();
    }
  };

  const handleTextareaInput = (e: React.FormEvent<HTMLTextAreaElement>) => {
    const target = e.target as HTMLTextAreaElement;
    target.style.height = "auto";
    target.style.height = target.scrollHeight + "px";
  };

  const idle = !focused && input.trim().length === 0;

  return (
    <div
      className={`border-t border-slate-200/60 dark:border-slate-700/60 bg-white dark:bg-slate-900 px-6 transition-[padding] duration-200 ${
        idle ? "py-2" : "py-4"
      }`}
    >
      <div className="max-w-4xl mx-auto">
        <div className="relative">
          {/* Image Previews */}
          {uploadedImageArtifacts.length > 0 && (
            <div className="flex gap-3 mb-3 items-start flex-wrap">
              {uploadedImageArtifacts.map((artifact) => (
                <div key={artifact.artifactId} className="relative group">
                  <div className="w-32 h-32 md:w-40 md:h-40 rounded-xl overflow-hidden border border-orange-300 dark:border-orange-700 shadow-sm bg-slate-50 dark:bg-slate-800">
                    <img
                      src={`data:image/jpeg;base64,${artifact.data}`}
                      alt={artifact.fileName}
                      className="object-cover w-full h-full"
                    />
                  </div>
                  {onRemoveImageArtifact && (
                    <button
                      onClick={() => onRemoveImageArtifact(artifact.artifactId)}
                      className="absolute -top-2 -right-2 bg-orange-500 hover:bg-orange-600 text-white rounded-full p-1 shadow transition-colors"
                      aria-label="Remove image"
                    >
                      <svg
                        className="w-3 h-3"
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
                  )}
                  <div className="text-[10px] mt-1 text-center text-orange-600 dark:text-orange-400 w-32 md:w-40 truncate">
                    {artifact.fileName}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* File upload indicators - only show for data when no images */}
          {hasUploadedData && uploadedImageArtifacts.length === 0 && (
            <div className="flex gap-2 mb-3 items-center">
              <div className="flex items-center gap-2 px-3 py-2 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg">
                <svg
                  className="w-4 h-4 text-emerald-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
                <span className="text-sm text-emerald-700 dark:text-emerald-300">
                  Data uploaded
                </span>
              </div>
            </div>
          )}

          {/* Input container */}
          <div
            className={`relative flex items-end gap-3 rounded-2xl border border-slate-300/60 dark:border-slate-600/60 bg-white dark:bg-slate-800 shadow-lg hover:shadow-xl transition-[box-shadow,background,transform] duration-200 overflow-hidden ${
              idle ? "scale-[0.98]" : "scale-100"
            }`}
          >
            {/* Attachment button */}
            <div className="relative p-3">
              <button
                ref={attachmentButtonRef}
                type="button"
                onClick={() => setPickerOpen(!pickerOpen)}
                data-attachment-button
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
              <AttachmentPicker
                isOpen={pickerOpen}
                onClose={() => setPickerOpen(false)}
                onImageSelect={() => fileInputImageRef.current?.click()}
                onCsvSelect={() => fileInputCsvRef.current?.click()}
                sessionId={sessionId}
                attachmentButtonRef={attachmentButtonRef}
              />
            </div>

            {/* Text input */}
            <div className={`flex-1 ${idle ? "py-2" : "py-3"} pr-3`}>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                placeholder={
                  uploadedImageArtifacts.length > 0 && hasUploadedData
                    ? "Ask questions about your images and data..."
                    : uploadedImageArtifacts.length > 0
                    ? "Describe what you see or ask questions about the images..."
                    : hasUploadedData
                    ? "Ask questions about your data..."
                    : sessionId
                    ? "Ask questions about your data or upload files..."
                    : "Type your message here..."
                }
                rows={1}
                className={`w-full resize-none bg-transparent focus:outline-none text-sm leading-relaxed placeholder:text-slate-400 dark:placeholder:text-slate-500 max-h-32 transition-[min-height] duration-200 ${
                  idle ? "min-h-[1.1rem]" : "min-h-[1.5rem]"
                }`}
                style={{
                  height: "auto",
                  minHeight: idle ? "1.1rem" : "1.5rem",
                }}
                onInput={handleTextareaInput}
              />
            </div>

            {/* Send button */}
            <div className={`p-${idle ? "2" : "3"}`}>
              <button
                onClick={onSend}
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
      </div>
    </div>
  );
};
