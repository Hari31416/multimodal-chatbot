import React, { useState, useEffect, useRef } from "react";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";

interface AnalysisCodeBlockProps {
  code: string;
}

/**
 * Displays Python analysis code with copy & wrap controls.
 * Separated for future enhancements (e.g., run locally, diffing, etc.).
 */
hljs.registerLanguage("python", python);

export const AnalysisCodeBlock: React.FC<AnalysisCodeBlockProps> = ({
  code,
}) => {
  const [open, setOpen] = useState(false);
  const codeRef = useRef<HTMLElement | null>(null);
  if (!code) return null;

  useEffect(() => {
    if (open && codeRef.current) {
      try {
        hljs.highlightElement(codeRef.current);
      } catch {}
    }
  }, [open, code]);

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
        <div id="analysis-code-block">
          <div className="relative group/code border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm dark:shadow-inner transition-colors overflow-hidden bg-[#fafafa] dark:bg-[#1e1e24]">
            <div className="absolute top-0 left-0 right-0 h-8 flex items-center justify-between px-2 bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-b border-slate-200 dark:border-slate-700/50">
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase tracking-wide font-semibold text-teal-700 dark:text-teal-300 px-1.5 py-0.5 bg-teal-100/80 dark:bg-teal-900/50 rounded-md ring-1 ring-teal-400/30">
                  python
                </span>
              </div>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => {
                    navigator.clipboard.writeText(code);
                  }}
                  className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-teal-600/80 text-white hover:bg-teal-500/80 focus:outline-none focus:ring-2 focus:ring-teal-500 transition-colors"
                >
                  Copy
                </button>
              </div>
            </div>
            <pre className="mt-8 overflow-x-auto whitespace-pre p-4 pt-2 text-[13px] leading-relaxed font-mono">
              <code ref={codeRef} className="language-python hljs">
                {code}
              </code>
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
