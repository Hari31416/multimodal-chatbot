const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function postJSON<T>(path: string, body: any): Promise<T> {
  const r = await fetch(base + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function postForm<T>(path: string, form: FormData): Promise<T> {
  const r = await fetch(base + path, { method: "POST", body: form });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
