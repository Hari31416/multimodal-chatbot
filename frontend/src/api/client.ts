// Shared API base URL so other modules (e.g. startup health check) can reuse it
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function postJSON<T>(path: string, body: any): Promise<T> {
  const r = await fetch(API_BASE_URL + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function postForm<T>(path: string, form: FormData): Promise<T> {
  const r = await fetch(API_BASE_URL + path, { method: "POST", body: form });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function getJSON<T>(path: string): Promise<T> {
  const r = await fetch(API_BASE_URL + path, { method: "GET" });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function deleteJSON<T>(path: string): Promise<T> {
  const r = await fetch(API_BASE_URL + path, { method: "DELETE" });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
