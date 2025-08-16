import React, { useEffect } from "react";
import { DatasetOverview } from "./DatasetOverview";

interface DatasetModalProps {
  open: boolean;
  onClose: () => void;
  columns: string[];
  head: any[][];
}

export const DatasetModal: React.FC<DatasetModalProps> = ({
  open,
  onClose,
  columns,
  head,
}) => {
  useEffect(() => {
    function handler(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (open) window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-[10000] flex items-start md:items-center justify-center p-4 md:p-8 bg-slate-900/70 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
    >
      <div className="relative w-full max-w-4xl max-h-full overflow-y-auto rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
        <div className="sticky top-0 flex items-center justify-between gap-4 px-5 py-3 border-b border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur">
          <div className="flex items-center gap-2">
            <span className="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-300 flex items-center justify-center text-sm">
              📊
            </span>
            <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
              Dataset Overview
            </h2>
            <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">
              {columns.length} columns • {head.length} preview rows
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-2 py-1 rounded-md text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition"
            >
              Close
            </button>
          </div>
        </div>
        <div className="p-5">
          <DatasetOverview columns={columns} head={head} />
        </div>
      </div>
    </div>
  );
};
