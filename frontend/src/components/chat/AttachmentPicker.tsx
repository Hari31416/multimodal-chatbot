import React, { useRef } from "react";
import { createPortal } from "react-dom";

interface AttachmentPickerProps {
  isOpen: boolean;
  onClose: () => void;
  onImageSelect: () => void;
  onCsvSelect: () => void;
  sessionId: string | null;
  attachmentButtonRef: React.RefObject<HTMLButtonElement>;
}

export const AttachmentPicker: React.FC<AttachmentPickerProps> = ({
  isOpen,
  onClose,
  onImageSelect,
  onCsvSelect,
  sessionId,
  attachmentButtonRef,
}) => {
  const pickerRef = useRef<HTMLDivElement | null>(null);

  if (!isOpen || !attachmentButtonRef.current) {
    return null;
  }

  return createPortal(
    <div
      ref={pickerRef}
      data-picker
      className="fixed w-52 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-2xl z-[9999] overflow-hidden"
      style={{
        bottom:
          window.innerHeight -
          attachmentButtonRef.current.getBoundingClientRect().top +
          8,
        left: attachmentButtonRef.current.getBoundingClientRect().left,
      }}
    >
      <div className="py-2">
        <button
          className="flex items-center w-full text-left px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors group"
          onClick={() => {
            onClose();
            onImageSelect();
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
            onClose();
            onCsvSelect();
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
  );
};
