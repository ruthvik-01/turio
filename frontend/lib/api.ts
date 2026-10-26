import type { Application, Field, Method, Run } from "@/lib/types";

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
  let response: Response;
  try {
    response = await fetch(`/api${path}`, { ...options, headers, cache: "no-store", credentials: "same-origin",
      signal: options.signal || AbortSignal.timeout(["GET", "HEAD"].includes(options.method || "GET") ? 60000 : 310000) });
  } catch (error) {
    if (error instanceof DOMException && error.name === "TimeoutError") throw new ApiError("The request took too long. Reload to try again; check an application's status before retrying submission.", 504, "REQUEST_TIMEOUT");
    throw error;
  }
  const payload = await response.json() as ApiEnvelope<T>;
  if (!response.ok || payload.error) throw new ApiError(payload.error?.message || "The request failed.", response.status, payload.error?.code || "REQUEST_FAILED");
  return payload.data as T;
}
export function requestKey(): Record<string, string> { return { "Idempotency-Key": crypto.randomUUID() }; }

export type ApplicationAnswerInput = { field_id: string; value: Field["value"]; user_confirmed: boolean; save_for_reuse: boolean; ai_confirmed?: boolean };

/** Retry a stale save only when its edited fields still match the user's baseline. */
export async function saveApplicationAnswers(application: Application, answers: ApplicationAnswerInput[], headers = requestKey()): Promise<Application> {
  const path = `/applications/${application.id}`;
  const save = (revision: number, key: Record<string, string>) => api<Application>(path + "/answers", {
    method: "POST", headers: key, body: JSON.stringify({ expected_revision: revision, answers }),
  });
  try { return await save(application.revision, headers); }
  catch (error) {
    if (!(error instanceof ApiError) || error.code !== "STALE_REVISION") throw error;
    const latest = await api<Application>(path);
    const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);
    const editable = ["created", "needs_input", "ready_for_review", "automation_failed"].includes(latest.status);
    const safe = answers.every(item => {
      const before = application.fields.find(field => field.id === item.field_id);
      const now = latest.fields.find(field => field.id === item.field_id);
      return before && now && ["field_key", "label", "input_type", "required", "normalized_intent", "options", "help_text", "value_source", "user_confirmed", "ai_confidence", "ai_winner_probability", "ai_uncertain"]
        .every(key => same(before[key as keyof Field], now[key as keyof Field])) && same(before.value, now.value);
    });
    if (!editable || !safe) throw new ApiError("These fields changed elsewhere. Your edits are still on screen. Check status to load the latest answers before saving again.", 409, "STALE_REVISION");
    return save(latest.revision, requestKey());
  }
}

export function safeExternalUrl(value: string | null): string | undefined {
  if (!value) return undefined;
  try { const url = new URL(value); return ["https:", "http:"].includes(url.protocol) ? url.href : undefined; } catch { return undefined; }
}

/** Queue only database work. Application submission never passes through here. */
export async function runTask<T>(kind: Run["kind"], method?: Method, onProgress?: (run: Run) => void): Promise<T> {
  let run = await api<Run>("/runs", {
    method: "POST", headers: requestKey(), body: JSON.stringify({ kind, ...(method ? { method } : {}) }),
  });
  const deadline = Date.now() + 30 * 60 * 1000;
  let delay = 750;
  while (true) {
    onProgress?.(run);
    if (run.state === "succeeded") return run.result as T;
    if (["failed", "interrupted", "cancelled"].includes(run.state)) {
      throw new ApiError(run.error_message || `Run ${run.state}.`, 409, run.error_code || "RUN_STOPPED");
    }
    if (Date.now() >= deadline) {
      throw new ApiError(`Run ${run.id} is still ${run.state}. It remains saved; check the worker and retry to reconnect.`, 408, "RUN_PENDING");
    }
    await new Promise(resolve => setTimeout(resolve, delay));
    delay = Math.min(Math.round(delay * 1.5), 5000);
    run = await api<Run>(`/runs/${run.id}`);
  }
}
