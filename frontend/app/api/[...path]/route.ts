import { createHash } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const base = (process.env.INTERNAL_API_BASE_URL || "http://127.0.0.1:18080/api/v1").replace(/\/$/, "");
type Tokens = { access_token: string; refresh_token: string; expires_in: number };
const refreshes = new Map<string, { expires: number; promise: Promise<Tokens | null> }>();
const allowed = new Set(["auth", "health", "profiles", "resumes", "jobs", "matches", "applications", "runs"]);

function error(message: string, status: number) {
  return NextResponse.json({ data: null, error: { code: status === 401 ? "UNAUTHENTICATED" : "REQUEST_FAILED", message }, request_id: null }, { status });
}
function setTokens(response: NextResponse, tokens: Tokens, secure: boolean) {
  const options = { httpOnly: true, sameSite: "lax" as const, secure, path: "/" };
  response.cookies.set("turio_access", tokens.access_token, { ...options, maxAge: tokens.expires_in });
  response.cookies.set("turio_refresh", tokens.refresh_token, { ...options, maxAge: 30 * 86400 });
}
function clearTokens(response: NextResponse) {
  response.cookies.delete("turio_access");
  response.cookies.delete("turio_refresh");
}
function publicOrigin(request: NextRequest) {
  const host = request.headers.get("x-forwarded-host")?.split(",")[0].trim()
    || request.headers.get("host")
    || request.nextUrl.host;
  const protocol = request.headers.get("x-forwarded-proto")?.split(",")[0].trim()
    || request.nextUrl.protocol.replace(":", "");
  return `${protocol}://${host}`;
}
function isSameOriginMutation(request: NextRequest) {
  const expected = publicOrigin(request);
  const origin = request.headers.get("origin");
  if (origin) return origin === expected;
  const referer = request.headers.get("referer");
  if (!referer || request.headers.get("sec-fetch-site") !== "same-origin") return false;
  try { return new URL(referer).origin === expected; } catch { return false; }
}
async function refresh(token: string): Promise<Tokens | null> {
  const now = Date.now();
  for (const [key, entry] of refreshes) if (entry.expires < now) refreshes.delete(key);
  const key = createHash("sha256").update(token).digest("hex");
  const existing = refreshes.get(key);
  if (existing) return existing.promise;
  const promise = (async () => {
    const response = await fetch(`${base}/auth/refresh`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: token }), cache: "no-store",
      signal: AbortSignal.timeout(15000),
    });
    if (!response.ok) return null;
    return (await response.json()).data.token as Tokens;
  })();
  refreshes.set(key, { promise, expires: now + 30000 });
  return promise;
}
async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (!allowed.has(path[0]) || path.some(s => s === ".." || s.includes("/") || s.includes("\\"))) return error("Unknown API path.", 404);
  const local = ["localhost", "127.0.0.1", "[::1]"].includes(request.nextUrl.hostname);
  const secure = request.nextUrl.protocol === "https:";
  if (!secure && !local) return error("HTTPS is required for authenticated sessions.", 403);
  if (!["GET", "HEAD"].includes(request.method) && !isSameOriginMutation(request)) return error("A same-origin request is required.", 403);
  const resource = path.map(encodeURIComponent).join("/");
  const authAction = path[0] === "auth" ? path[1] : null;
  if (authAction === "refresh") return error("Sessions are refreshed by the server.", 404);
  let tokens: Tokens | null = null;
  let access = request.cookies.get("turio_access")?.value;
  const refreshToken = request.cookies.get("turio_refresh")?.value;
  try {
    let body: Uint8Array | undefined;
    if (request.body) {
      const reader = request.body.getReader();
      const chunks: Uint8Array[] = [];
      let length = 0;
      while (true) {
        const chunk = await reader.read();
        if (chunk.done) break;
        length += chunk.value.length;
        if (length > 6 * 1024 * 1024) { await reader.cancel(); return error("Request exceeds the upload limit.", 413); }
        chunks.push(chunk.value);
      }
      body = Buffer.concat(chunks);
    }
    const login = authAction === "login" || authAction === "register";
    if (!login && !access && refreshToken) { tokens = await refresh(refreshToken); access = tokens?.access_token; }
    const upstream = async () => {
      const headers = new Headers();
      if (request.headers.has("content-type")) headers.set("content-type", request.headers.get("content-type")!);
      if (request.headers.has("idempotency-key")) headers.set("idempotency-key", request.headers.get("idempotency-key")!);
      if (access) headers.set("authorization", `Bearer ${access}`);
      let payload = body;
      if (authAction === "logout") {
        headers.set("content-type", "application/json");
        payload = Buffer.from(JSON.stringify({ refresh_token: tokens?.refresh_token || refreshToken || "" }));
      }
      return fetch(`${base}/${resource}${request.nextUrl.search}`, {
        method: request.method, headers, body: payload as BodyInit | undefined,
        cache: "no-store", signal: AbortSignal.timeout(["GET", "HEAD"].includes(request.method) ? 15000 : 300000),
      });
    };
    let result = await upstream();
    if (result.status === 401 && !login && refreshToken && !tokens) {
      tokens = await refresh(refreshToken);
      if (tokens) { access = tokens.access_token; result = await upstream(); }
    }
    const payload = await result.json();
    if (login && result.ok) { tokens = payload.data.token; delete payload.data.token; }
    const response = NextResponse.json(payload, { status: result.status, headers: { "Cache-Control": "no-store" } });
    if (result.headers.has("retry-after")) response.headers.set("Retry-After", result.headers.get("retry-after")!);
    if (tokens) setTokens(response, tokens, secure);
    if (result.status === 401 || ((authAction === "logout" || authAction === "logout-all") && result.ok)) clearTokens(response);
    return response;
  } catch {
    const response = error("The API could not be reached. Check that the backend and database are running.", 503);
    if (tokens) setTokens(response, tokens, secure);
    return response;
  }
}
export { proxy as GET, proxy as POST, proxy as PATCH, proxy as DELETE };
