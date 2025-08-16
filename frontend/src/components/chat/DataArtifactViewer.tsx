import React from "react";

interface DataArtifactViewerProps {
  chart?: string;
  text?: string;
  raw?: string;
  isMime?: boolean;
}

/**
 * Renders artifact returned from the /analyze endpoint.
 * Keeps presentation concerns isolated from ChatMessage.
 */
export const DataArtifactViewer: React.FC<DataArtifactViewerProps> = ({
  chart,
  text,
  raw,
  isMime,
}) => {
  if (!chart && !text) return null;
  return (
    <div className="space-y-4">
      {chart && (
        <div className="rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm bg-white dark:bg-slate-800/50">
          <img
            src={chart}
            alt="Analysis chart"
            className="w-full max-h-96 object-contain"
            loading="lazy"
          />
        </div>
      )}
      {text && (
        <pre className="text-xs leading-relaxed whitespace-pre-wrap break-words font-mono bg-slate-950/5 dark:bg-slate-700/30 p-3 rounded-lg border border-slate-200 dark:border-slate-700">
          {text}
        </pre>
      )}
      {process.env.NODE_ENV === "development" && raw && !chart && !text && (
        <details className="text-[10px] opacity-70">
          <summary className="cursor-pointer">Raw Artifact</summary>
          <pre className="mt-2 whitespace-pre-wrap break-words">{raw}</pre>
        </details>
      )}
    </div>
  );
};
