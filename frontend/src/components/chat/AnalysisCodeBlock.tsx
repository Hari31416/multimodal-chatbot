import React, { useState } from "react";
import { CodeBlock } from "./CodeBlock";

interface AnalysisCodeBlockProps {
  code: string;
}

/**
 * Displays Python analysis code with copy & wrap controls.
 * Separated for future enhancements (e.g., run locally, diffing, etc.).
 */
export const AnalysisCodeBlock: React.FC<AnalysisCodeBlockProps> = ({
  code,
}) => {
  const [open, setOpen] = useState(false);
  if (!code) return null;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 pl-1">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="flex items-center gap-2 text-xs font-semibold tracking-wide px-2 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
          aria-expanded={open}
          aria-controls="analysis-code-block"
        >
          <span
            className={`inline-block transition-transform w-3 h-3 text-slate-500 dark:text-slate-400 ${
              open ? "rotate-90" : ""
            }`}
          >
            ▶
          </span>
          <span>{open ? "Hide Analysis Code" : "Show Analysis Code"}</span>
        </button>
        {open && (
          <span className="text-[10px] uppercase tracking-wide font-semibold text-indigo-600 dark:text-indigo-400 bg-indigo-100/60 dark:bg-indigo-900/30 px-1.5 py-0.5 rounded">
            Python
          </span>
        )}
      </div>
      {open && (
        <div id="analysis-code-block" className="pt-1">
          <CodeBlock className="language-python">{code}</CodeBlock>
        </div>
      )}
    </div>
  );
};
