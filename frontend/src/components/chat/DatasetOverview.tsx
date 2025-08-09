import React, { useState } from "react";

interface DatasetOverviewProps {
  columns: string[];
  head: any[][];
}

export const DatasetOverview: React.FC<DatasetOverviewProps> = ({
  columns,
  head,
}) => {
  const [showDatasetOverview, setShowDatasetOverview] = useState(true);

  if (columns.length === 0) {
    return null;
  }

  return (
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
            aria-label={
              showDatasetOverview
                ? "Hide dataset overview"
                : "Show dataset overview"
            }
          >
            <svg
              className={`w-4 h-4 text-slate-500 dark:text-slate-400 transition-transform ${
                showDatasetOverview ? "rotate-180" : ""
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        </div>
      </div>
      {showDatasetOverview && (
        <div className="p-4 space-y-3">
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
      )}
    </div>
  );
};
