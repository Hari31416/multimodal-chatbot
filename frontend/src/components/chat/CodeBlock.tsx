import React, { useState, useEffect, useRef } from "react";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import javascript from "highlight.js/lib/languages/javascript";
import typescript from "highlight.js/lib/languages/typescript";
import jsonLang from "highlight.js/lib/languages/json";
import bash from "highlight.js/lib/languages/bash";
import latex from "highlight.js/lib/languages/latex";

// Register common languages once
try {
  hljs.registerLanguage("python", python);
  hljs.registerLanguage("javascript", javascript);
  hljs.registerLanguage("typescript", typescript);
  hljs.registerLanguage("json", jsonLang);
  hljs.registerLanguage("bash", bash);
  hljs.registerLanguage("latex", latex);
  hljs.registerLanguage("tex", latex); // alias for latex
} catch {
  // ignore duplicate registration errors during HMR
}

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
  const [wrap, setWrap] = useState(() => {
    // Enable wrapping by default on mobile devices
    return window.innerWidth < 768;
  });
  const [expanded, setExpanded] = useState(false);
  const codeRef = useRef<HTMLElement | null>(null);

  // Update wrap state on window resize
  useEffect(() => {
    const handleResize = () => {
      const isMobile = window.innerWidth < 768;
      setWrap(isMobile);
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

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

  // Determine if children already contain span highlighting tokens (from rehype-highlight)
  const hasPreTokenized = (() => {
    // crude check: if any child is a React element with a class starting hljs-
    const inspect = (node: any): boolean => {
      if (!node) return false;
      if (Array.isArray(node)) return node.some(inspect);
      if (React.isValidElement(node)) {
        const cls = (node.props?.className || "") as string;
        if (/hljs-/.test(cls)) return true;
        return inspect(node.props?.children);
      }
      return false;
    };
    return inspect(children);
  })();

  useEffect(() => {
    if (!codeRef.current) return;
    if (hasPreTokenized) return; // already highlighted by rehype
    const lang = className?.match(/language-([\w+-]+)/)?.[1];
    if (!lang) return;
    try {
      const result = hljs.highlight(raw, { language: lang });
      codeRef.current.innerHTML = result.value;
    } catch {
      // fallback: leave plain text
    }
  }, [raw, className, hasPreTokenized]);

  return (
    <div
      className="relative not-prose group/code border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm dark:shadow-inner transition-colors overflow-hidden bg-[#fafafa] dark:bg-[#1e1e24] w-full max-w-full"
      style={{ alignSelf: "flex-start" }}
    >
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
        <div className="w-full overflow-hidden">
          <pre
            className={`${className || ""} mt-8 ${
              wrap
                ? "overflow-hidden whitespace-pre-wrap break-words"
                : "overflow-x-auto whitespace-pre"
            } w-full max-w-full p-4 pt-2 text-[13px] leading-relaxed font-mono bg-transparent border-none transition-colors ${
              wrap ? "md:text-[13px]" : ""
            }`}
          >
            <code
              ref={codeRef}
              className={`${className} hljs block text-slate-900 dark:text-slate-100 w-full max-w-full ${
                wrap ? "break-words" : ""
              }`}
            >
              {hasPreTokenized ? children : raw}
            </code>
          </pre>
        </div>
      </div>
    </div>
  );
};
