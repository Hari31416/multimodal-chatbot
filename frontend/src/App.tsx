import React, { useState, useEffect } from "react";
import UnifiedChat from "./components/UnifiedChat";
import { API_BASE_URL } from "./api/client";

const POLL_INTERVAL_MS = 2000; // 2s between health checks
const MAX_WAIT_MS = 120000; // Stop after 2 minutes with failure message

interface HealthStatus {
  ready: boolean;
  attempts: number;
  startedAt: number;
  lastError?: string;
  elapsedMs: number;
}

const BackendLoader: React.FC<{ status: HealthStatus }> = ({ status }) => {
  if (status.ready) return null;
  const pct = Math.min(95, Math.round((status.elapsedMs / MAX_WAIT_MS) * 100)); // cap at 95 until actually ready
  const seconds = Math.floor(status.elapsedMs / 1000);
  return (
    <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
      <div className="w-80 max-w-[90%] space-y-4">
        <h2 className="text-center text-lg font-semibold text-slate-700 dark:text-slate-200">
          Connecting to backend…
        </h2>
        <div className="w-full h-3 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 via-sky-500 to-cyan-400 transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="text-xs text-center text-slate-600 dark:text-slate-400">
          Attempt {status.attempts} · {seconds}s elapsed
          {status.lastError && (
            <>
              <br />
              Last error: {status.lastError}
            </>
          )}
        </p>
        {status.elapsedMs > MAX_WAIT_MS && (
          <p className="text-xs text-center text-rose-600 dark:text-rose-400">
            Backend still not responding. You can wait or refresh the page.
          </p>
        )}
      </div>
    </div>
  );
};

const App: React.FC = () => {
  const [dark, setDark] = useState<boolean>(
    () => window.matchMedia("(prefers-color-scheme: dark)").matches
  );
  const [health, setHealth] = useState<HealthStatus>(() => ({
    ready: false,
    attempts: 0,
    startedAt: Date.now(),
    elapsedMs: 0,
  }));
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  // Poll backend /health until ready
  useEffect(() => {
    let cancelled = false;
    let timer: any;
    async function poll() {
      setHealth((h) => ({
        ...h,
        attempts: h.attempts + 1,
        elapsedMs: Date.now() - h.startedAt,
      }));
      try {
        const r = await fetch(`${API_BASE_URL}/health`);
        if (!r.ok) throw new Error(r.status + " " + r.statusText);
        // Accept JSON or plain text "ok"
        let ok = false;
        const ct = r.headers.get("content-type") || "";
        if (ct.includes("application/json")) {
          try {
            const data = await r.json();
            ok = !!(
              data.status === "ok" ||
              data.ok ||
              data.healthy ||
              data.status === "healthy"
            );
          } catch {
            ok = false;
          }
        } else {
          const text = (await r.text()).toLowerCase();
          ok = text.includes("ok") || text.includes("healthy");
        }
        if (ok && !cancelled) {
          setHealth((h) => ({
            ...h,
            ready: true,
            elapsedMs: Date.now() - h.startedAt,
          }));
          return;
        }
        if (!cancelled) {
          timer = setTimeout(poll, POLL_INTERVAL_MS);
        }
      } catch (e: any) {
        if (!cancelled) {
          setHealth((h) => ({
            ...h,
            lastError: e.message,
            elapsedMs: Date.now() - h.startedAt,
          }));
          timer = setTimeout(poll, POLL_INTERVAL_MS);
        }
      }
    }
    poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, []);

  return (
    <div
      className="h-screen flex flex-col relative overflow-hidden"
      style={{ height: "calc(var(--vh, 1vh) * 100)" }}
    >
      <main className="flex-1 overflow-hidden relative">
        <UnifiedChat dark={dark} setDark={setDark} />
        <BackendLoader status={health} />
      </main>
    </div>
  );
};

export default App;
