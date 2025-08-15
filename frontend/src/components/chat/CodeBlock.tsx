import React, { useState } from "react";

// Utility: flatten React children to plain text (used for copy)
const extractText = (node: any): string => {
  if (node == null) return "";
  if (typeof node === "string") return node;
  if (Array.isArray(node)) return node.map(extractText).join("");
  if (React.isValidElement(node))
    return extractText((node as any).props?.children);
  return "";
};

interface CodeBlockProps {
  className?: string;
  children: React.ReactNode;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  className,
  children,
}) => {
  const [copied, setCopied] = useState(false);
  const [wrap, setWrap] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const raw = extractText(children).replace(/\s+$/g, "");
  const lang = className?.match(/language-([\w+-]+)/)?.[1];
  // We keep raw text only for copy button & potential future line features.
  // IMPORTANT: We must NOT replace the children (which may contain <span> tokens
  // inserted by rehype-highlight) with the raw string, otherwise we lose coloring.
  const lines = raw ? raw.split(/\n/) : [""];
  const collapseThreshold = 200; // raise threshold to effectively disable truncation in most cases
  const isCollapsible = lines.length > collapseThreshold;

  const handleCopy = () => {
    if (!raw) return;
    navigator.clipboard.writeText(raw).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    });
  };

  return (
    <div className="relative group/code border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm dark:shadow-inner transition-colors overflow-hidden bg-[#fafafa] dark:bg-[#1e1e24]">
      <div className="absolute top-0 left-0 right-0 h-8 flex items-center justify-between px-2 bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border-b border-slate-200 dark:border-slate-700/50">
        <div className="flex items-center gap-2">
          {lang && (
            <span className="text-[10px] uppercase tracking-wide font-semibold text-teal-700 dark:text-teal-300 px-1.5 py-0.5 bg-teal-100/80 dark:bg-teal-900/50 rounded-md ring-1 ring-teal-400/30">
              {lang}
            </span>
          )}
          {isCollapsible && (
            <button
              type="button"
              onClick={() => setExpanded((e) => !e)}
              className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-slate-200/70 dark:bg-slate-700/70 text-slate-700 dark:text-slate-300 hover:bg-slate-300/70 dark:hover:bg-slate-600/70 focus:outline-none focus:ring-2 focus:ring-teal-500 transition-colors"
            >
              {expanded ? "Collapse" : `Expand (${lines.length})`}
            </button>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => setWrap((w) => !w)}
            className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-slate-200/70 dark:bg-slate-700/70 text-slate-700 dark:text-slate-300 hover:bg-slate-300/70 dark:hover:bg-slate-600/70 focus:outline-none focus:ring-2 focus:ring-teal-500 transition-colors"
          >
            {wrap ? "No-Wrap" : "Wrap"}
          </button>
          <button
            type="button"
            onClick={handleCopy}
            className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-teal-600/80 text-white hover:bg-teal-500/80 focus:outline-none focus:ring-2 focus:ring-teal-500 transition-colors"
          >
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
      </div>
      <div className="relative">
        <pre
          className={`${className || ""} mt-8 overflow-x-auto ${
            wrap ? "whitespace-pre-wrap break-words" : "whitespace-pre"
          } p-4 pt-2 text-[13px] leading-relaxed font-mono bg-transparent border-none transition-colors`}
        >
          {/* Render original children to preserve <span class="hljs-..."> tokens */}
          <code
            className={`${className} hljs block text-slate-900 dark:text-slate-100`}
          >
            {children}
          </code>
        </pre>
      </div>
    </div>
  );
};
