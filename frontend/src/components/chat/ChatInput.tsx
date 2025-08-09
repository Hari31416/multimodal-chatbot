import React, { useRef } from "react";
import { AttachmentPicker } from "./AttachmentPicker";

interface ChatInputProps {
  input: string;
  setInput: (input: string) => void;
  pending: boolean;
  imageFile: File | null;
  setImageFile: (file: File | null) => void;
  sessionId: string | null;
  pickerOpen: boolean;
  setPickerOpen: (open: boolean) => void;
  onSend: () => void;
  error: string;
  fileInputImageRef: React.RefObject<HTMLInputElement>;
  fileInputCsvRef: React.RefObject<HTMLInputElement>;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  input,
  setInput,
  pending,
  imageFile,
  setImageFile,
  sessionId,
  pickerOpen,
  setPickerOpen,
  onSend,
  error,
  fileInputImageRef,
  fileInputCsvRef,
}) => {
  const attachmentButtonRef = useRef<HTMLButtonElement | null>(null);

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

  const removeImageFile = () => {
    setImageFile(null);
    if (fileInputImageRef.current) {
      fileInputImageRef.current.value = "";
    }
  };

  return (
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
                  onClick={removeImageFile}
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
            <div className="flex-1 py-3 pr-3">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
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
                onInput={handleTextareaInput}
              />
            </div>

            {/* Send button */}
            <div className="p-3">
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
