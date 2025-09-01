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
  onRemoveCsvArtifact?: () => void;
  uploadProgress?: { [fileName: string]: number };
  uploadedCsvArtifact?: {
    artifactId: string;
    fileName: string;
    description: string;
    columns: string[];
    rowCount: number;
  } | null;
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
  onRemoveCsvArtifact,
  uploadProgress = {},
  uploadedCsvArtifact = null,
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
      className={`border-t border-slate-200/60 dark:border-slate-700/60 bg-white dark:bg-slate-900 px-2 sm:px-4 md:px-6 transition-[padding] duration-200 ${
        idle ? "py-2" : "py-4"
      }`}
    >
      <div className="max-w-4xl mx-auto">
        <div className="relative">
          {/* Image Previews and Upload Progress */}
          {(uploadedImageArtifacts.length > 0 ||
            Object.keys(uploadProgress).length > 0) && (
            <div className="flex gap-3 mb-3 items-start flex-wrap">
              {/* Show progress for files being uploaded */}
              {Object.entries(uploadProgress).map(([fileName, progress]) => (
                <div key={`uploading-${fileName}`} className="relative group">
                  <div className="w-32 h-32 md:w-40 md:h-40 rounded-xl overflow-hidden border border-blue-300 dark:border-blue-700 shadow-sm bg-slate-50 dark:bg-slate-800 flex items-center justify-center">
                    <div className="text-center">
                      <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                      <div className="text-xs text-blue-600 dark:text-blue-400 font-medium">
                        {progress}%
                      </div>
                    </div>
                  </div>
                  <div className="text-[10px] mt-1 text-center text-blue-600 dark:text-blue-400 w-32 md:w-40 truncate">
                    Uploading {fileName}
                  </div>
                  {/* Progress bar */}
                  <div className="absolute bottom-6 left-1 right-1 h-1 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 transition-all duration-300 ease-out"
                      style={{ width: `${progress}%` }}
                    ></div>
                  </div>
                </div>
              ))}

              {/* Show uploaded images */}
              {uploadedImageArtifacts.map((artifact) => (
                <div key={artifact.artifactId} className="relative group">
                  <div className="w-32 h-32 md:w-40 md:h-40 rounded-xl overflow-hidden border border-orange-300 dark:border-orange-700 shadow-sm bg-slate-50 dark:bg-slate-800">
                    <img
                      src={`data:image/png;base64,${artifact.data}`}
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

          {/* CSV Preview */}
          {uploadedCsvArtifact && (
            <div className="flex gap-3 mb-3 items-start flex-wrap">
              {/* Show progress for CSV files being uploaded */}
              {Object.entries(uploadProgress)
                .filter(([fileName]) => fileName.toLowerCase().endsWith(".csv"))
                .map(([fileName, progress]) => (
                  <div
                    key={`uploading-csv-${fileName}`}
                    className="relative group"
                  >
                    <div className="w-32 h-32 md:w-40 md:h-40 rounded-xl overflow-hidden border border-blue-300 dark:border-blue-700 shadow-sm bg-slate-50 dark:bg-slate-800 flex items-center justify-center">
                      <div className="text-center">
                        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                        <div className="text-xs text-blue-600 dark:text-blue-400 font-medium">
                          {progress}%
                        </div>
                      </div>
                    </div>
                    <div className="text-[10px] mt-1 text-center text-blue-600 dark:text-blue-400 w-32 md:w-40 truncate">
                      Uploading {fileName}
                    </div>
                    {/* Progress bar */}
                    <div className="absolute bottom-6 left-1 right-1 h-1 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 transition-all duration-300 ease-out"
                        style={{ width: `${progress}%` }}
                      ></div>
                    </div>
                  </div>
                ))}

              {/* Show uploaded CSV preview if no CSV is being uploaded */}
              {uploadedCsvArtifact &&
                Object.keys(uploadProgress).every(
                  (fileName) => !fileName.toLowerCase().endsWith(".csv")
                ) && (
                  <div className="relative group">
                    <div className="w-32 h-32 md:w-40 md:h-40 rounded-xl overflow-hidden border border-emerald-300 dark:border-emerald-700 shadow-sm bg-slate-50 dark:bg-slate-800 flex items-center justify-center">
                      {/* CSV File Icon */}
                      <svg
                        className="w-12 h-12 text-emerald-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                    </div>
                    {onRemoveCsvArtifact && (
                      <button
                        onClick={onRemoveCsvArtifact}
                        className="absolute -top-2 -right-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-full p-1 shadow transition-colors"
                        aria-label="Remove CSV file"
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
                    <div className="text-[10px] mt-1 text-center text-emerald-600 dark:text-emerald-400 w-32 md:w-40">
                      <div className="truncate font-medium">
                        {uploadedCsvArtifact.fileName}
                      </div>
                      <div className="text-[9px] mt-0.5 opacity-75">
                        {uploadedCsvArtifact.columns.length} cols,{" "}
                        {uploadedCsvArtifact.rowCount} rows
                      </div>
                    </div>
                  </div>
                )}
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
