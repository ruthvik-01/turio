/** The response envelope every backend route returns (API_SPEC.md section 8). */
export type ApiEnvelope<T> = {
  data: T | null;
  error: { code: string; message: string } | null;
  request_id: string | null;
};

export type HealthData = {
  status: string;
  database: string;
  version: string;
};

function apiBaseUrl(): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!baseUrl) {
    throw new Error(
      "NEXT_PUBLIC_API_BASE_URL is not set. It is inlined at build time, so it must be supplied as a build argument - see docker-compose.yml.",
    );
  }
  return baseUrl;
}

/**
 * Calls the backend health endpoint.
 *
 * Deliberately a browser-side fetch rather than a server-side one: the Phase 0
 * exit checklist needs the browser -> API path that every later screen depends
 * on to be the path that is proven.
 */
export async function fetchHealth(): Promise<ApiEnvelope<HealthData>> {
  const response = await fetch(`${apiBaseUrl()}/health`, { cache: "no-store" });
  return (await response.json()) as ApiEnvelope<HealthData>;
}
