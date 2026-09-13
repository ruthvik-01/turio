"use client";

import { useEffect, useState } from "react";

import { fetchHealth, type ApiEnvelope, type HealthData } from "@/lib/api";

type HealthState =
  | { kind: "loading" }
  | { kind: "loaded"; envelope: ApiEnvelope<HealthData> }
  | { kind: "failed"; message: string };

/**
 * Phase 0 diagnostic shell.
 *
 * Not a product screen: it exists so the phase exit checklist can prove the
 * frontend boots and reaches the API from the browser. Real screens, layout
 * and visual direction are Phase 1+ work owned by FRONTEND.md.
 */
export default function HomePage() {
  const [state, setState] = useState<HealthState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;

    fetchHealth()
      .then((envelope) => {
        if (!cancelled) {
          setState({ kind: "loaded", envelope });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setState({
            kind: "failed",
            message: error instanceof Error ? error.message : String(error),
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="mx-auto max-w-xl p-8">
      <h1 className="text-xl font-semibold">Turio</h1>
      <p className="mt-1 text-sm text-neutral-500">Phase 0 foundations shell</p>

      <section className="mt-6 rounded border border-neutral-300 p-4 text-sm">
        <h2 className="font-medium">Backend health</h2>
        {state.kind === "loading" && <p className="mt-2 text-neutral-500">Checking...</p>}
        {state.kind === "failed" && <p className="mt-2 text-red-700">{state.message}</p>}
        {state.kind === "loaded" && (
          <dl className="mt-2 space-y-1">
            <Row label="status" value={state.envelope.data?.status ?? "-"} />
            <Row label="database" value={state.envelope.data?.database ?? "-"} />
            <Row label="version" value={state.envelope.data?.version ?? "-"} />
            <Row label="error" value={state.envelope.error?.code ?? "none"} />
            <Row label="request_id" value={state.envelope.request_id ?? "-"} />
          </dl>
        )}
      </section>
    </main>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-3">
      <dt className="w-28 shrink-0 text-neutral-500">{label}</dt>
      <dd className="font-mono break-all">{value}</dd>
    </div>
  );
}
