import type { Method, Run } from "@/lib/types";

/** The response envelope every backend route returns (API_SPEC.md section 8). */
export type ApiEnvelope<T> = {
  data: T | null;
  error: { code: string; message: string } | null;
  request_id: string | null;
};

export class ApiError extends Error {
  constructor(message: string, public status: number, public code: string) { super(message); }
}

/** Same-origin proxy; credentials never enter client JavaScript. */
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const response = await fetch(`/api${path}`, { ...options, headers, cache: "no-store", credentials: "same-origin" });
  const payload = await response.json() as ApiEnvelope<T>;
  if (!response.ok || payload.error) throw new ApiError(payload.error?.message || "The request failed.", response.status, payload.error?.code || "REQUEST_FAILED");
  return payload.data as T;
}
export function requestKey(): Record<string, string> { return { "Idempotency-Key": crypto.randomUUID() }; }
export function safeExternalUrl(value: string | null): string | undefined {
  if (!value) return undefined;
  try { const url = new URL(value); return ["https:", "http:"].includes(url.protocol) ? url.href : undefined; } catch { return undefined; }
}

/** Queue only database work. Application submission never passes through here. */
export async function runTask<T>(kind: Run["kind"], method?: Method, onProgress?: (run: Run) => void): Promise<T> {
  let run = await api<Run>("/runs", {
    method: "POST", headers: requestKey(), body: JSON.stringify({ kind, ...(method ? { method } : {}) }),
  });
  const deadline = Date.now() + 5 * 60 * 1000;
  while (true) {
    onProgress?.(run);
    if (run.state === "succeeded") return run.result as T;
    if (["failed", "interrupted", "cancelled"].includes(run.state)) {
      throw new ApiError(run.error_message || `Run ${run.state}.`, 409, run.error_code || "RUN_STOPPED");
    }
    if (Date.now() >= deadline) {
      throw new ApiError(`Run ${run.id} is still ${run.state}. It remains saved; check the worker and retry to reconnect.`, 408, "RUN_PENDING");
    }
    await new Promise(resolve => setTimeout(resolve, 750));
    run = await api<Run>(`/runs/${run.id}`);
  }
}
