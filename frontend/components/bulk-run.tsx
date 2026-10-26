"use client";
import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from "react";
import { api, ApiError, requestKey, saveApplicationAnswers } from "@/lib/api";
import { approvalFingerprint, automaticBlocker, batchApprovalFresh } from "@/lib/bulk";
import type { Application, Job, Profile } from "@/lib/types";

export type BulkResult = { job: Job; application?: Application; error?: string; stage?: "prepare" | "review" | "submit" };
export type BulkProgress = { done: number; total: number; label: string };

type Context = {
  running: boolean;
  progress: BulkProgress | null;
  notice: string;
  error: string;
  results: Record<string, BulkResult>;
  heldForReview: Record<string, boolean>;
  unavailable: Record<string, true>;
  acknowledgeUnavailable: (ids: string[]) => void;
  setHeldForReview: (update: (previous: Record<string, boolean>) => Record<string, boolean>) => void;
  setError: (value: string) => void;
  setNotice: (value: string) => void;
  prepare: (jobs: Job[], options: { automatic: boolean; aiConsent: boolean }) => Promise<void>;
  submitReady: () => Promise<void>;
  requestStop: () => void;
  clear: () => void;
  mergeResults: (applications: Application[]) => void;
  refreshResults: (ids: string[]) => Promise<void>;
};

const BulkRunContext = createContext<Context | null>(null);

export function BulkRunProvider({ children }: { children: ReactNode }) {
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState<BulkProgress | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [results, setResults] = useState<Record<string, BulkResult>>({});
  const [heldForReview, setHeldForReviewState] = useState<Record<string, boolean>>({});
  const [unavailable, setUnavailable] = useState<Record<string, true>>({});
  const stopRef = useRef(false);
  const keys = useRef<Record<string, Record<string, string>>>({});
  const submitKeys = useRef<Record<string, Record<string, string>>>({});
  const resultsRef = useRef<Record<string, BulkResult>>({});
  const heldRef = useRef<Record<string, boolean>>({});

  const write = useCallback((next: Record<string, BulkResult>) => {
    resultsRef.current = next;
    setResults(next);
  }, []);
  const setHeldForReview = useCallback((update: (previous: Record<string, boolean>) => Record<string, boolean>) => {
    const next = update(heldRef.current);
    heldRef.current = next;
    setHeldForReviewState(next);
  }, []);
  const mergeResults = useCallback((applications: Application[]) => {
    // Keyed by job id so a run started on either page resolves to the same entry.
    write({ ...resultsRef.current,
      ...Object.fromEntries(applications.map(application => [application.job.id,
        { job: application.job, application, stage: "prepare" as const }])) });
  }, [write]);
  const refreshResults = useCallback(async (ids: string[]) => {
    const next = { ...resultsRef.current };
    for (const id of ids) {
      const result = next[id];
      if (!result?.application) continue;
      try {
        const application = await api<Application>(`/applications/${result.application.id}`);
        next[id] = { ...result, application, error: result.stage === "submit" ? result.error : undefined };
      } catch { /* Keep the last known state; the page reload will reconcile. */ }
    }
    write(next);
  }, [write]);

  async function submitPrepared(prepared: Record<string, BulkResult>, approvedAt: number) {
    // The prepared set is the queue; selection is page-local and must not gate a run
    // that may have started on a different route.
    const queue = Object.values(prepared).filter(result => result.application && !result.error && !heldRef.current[result.job.id] && automaticBlocker(result.application) === null)
      .map(result => ({ ...result, fingerprint: approvalFingerprint(result.application!) }));
    const next = { ...prepared };
    let approvalExpired = false;
    setRunning(true); setError(""); stopRef.current = false;
    try {
      for (const [index, result] of queue.entries()) {
        if (stopRef.current) break;
        if (!batchApprovalFresh(approvedAt)) { approvalExpired = true; break; }
        let application = result.application!;
        let stage: "review" | "submit" = "review";
        setProgress({ done: index + 1, total: queue.length, label: `${result.job.company} — ${result.job.title}` });
        setNotice(`Submitting ${index + 1} of ${queue.length}: ${result.job.company} — ${result.job.title}.`);
        try {
          application = await api<Application>(`/applications/${application.id}`);
          const blocker = automaticBlocker(application);
          if (blocker) throw new Error(blocker);
          if (approvalFingerprint(application) !== result.fingerprint) throw new Error("Prepared job or answers changed. Review the updated details and approve again.");
          application = await api<Application>(`/applications/${application.id}/review`, { method: "POST" });
          if (automaticBlocker(application) || approvalFingerprint(application) !== result.fingerprint || !application.review_token) throw new Error("Review changed or expired. Open this application and review again.");
          if (!batchApprovalFresh(approvedAt)) { approvalExpired = true; throw new Error("Bulk approval expired. Approve remaining applications again."); }
          const token = application.review_token;
          const key = `${application.id}:${token}`;
          submitKeys.current[key] ||= requestKey();
          stage = "submit";
          application = await api<Application>(`/applications/${application.id}/approve-submit`, { method: "POST", headers: submitKeys.current[key], body: JSON.stringify({ approved: true, review_token: token }) });
          next[result.job.id] = { job: result.job, application, stage };
        } catch (caught) {
          if (caught instanceof ApiError && caught.code === "JOB_UNAVAILABLE") {
            delete next[result.job.id];
            setUnavailable(values => ({ ...values, [result.job.id]: true }));
          } else {
            if (stage === "submit") {
              try { application = await api<Application>(`/applications/${application.id}`); } catch { /* Check manually; never replay a submission. */ }
            }
            next[result.job.id] = { job: result.job, application, stage,
              error: application.status === "submitted" ? undefined : `${(caught as Error).message}${stage === "submit" ? " Check status in the application; no automatic retry." : ""}` };
          }
        }
        write({ ...next });
      }
      setNotice(approvalExpired ? "Bulk approval expired. Approve the remaining applications again." : stopRef.current ? "Stopped after the current job. Other applications remain pending." : "Automatic batch finished. Confirmed ready applications were submitted; missing answers, held and unsupported jobs remain pending.");
    } finally { setRunning(false); setProgress(null); }
  }

  const prepare = useCallback(async (jobs: Job[], options: { automatic: boolean; aiConsent: boolean }) => {
    if (!jobs.length) return;
    const approvedAt = Date.now();
    setRunning(true); setError(""); stopRef.current = false;
    const next = { ...resultsRef.current };
    try {
      const profileVersion = options.automatic ? (await api<Profile>("/profiles/me")).version : null;
      for (const [index, job] of jobs.entries()) {
        if (stopRef.current) break;
        setProgress({ done: index + 1, total: jobs.length, label: `${job.company} — ${job.title}` });
        setNotice(`Preparing ${index + 1} of ${jobs.length}: ${job.company} — ${job.title}.`);
        let application = next[job.id]?.application;
        try {
          keys.current[job.id] ||= requestKey();
          application ||= await api<Application>("/applications", { method: "POST", headers: keys.current[job.id], body: JSON.stringify({ job_id: job.id, reuse_existing: true }) });
          application = await api<Application>(`/applications/${application.id}`);
          if (["created", "automation_failed"].includes(application.status) || ((application.manual_submission_required || (options.automatic && application.profile_version !== profileVersion)) && ["needs_input", "ready_for_review"].includes(application.status))) {
            const capability = await api<{ available: boolean; reason: string | null }>(`/applications/${application.id}/capability`);
            if (!capability.available) throw new Error(capability.reason || "Agent preparation is unavailable for this job.");
            application = await api<Application>(`/applications/${application.id}/start`, { method: "POST", body: JSON.stringify({ ai_assist: options.aiConsent }) });
          }
          next[job.id] = { job, application, stage: "prepare" };
        } catch (caught) {
          next[job.id] = { job, application, stage: "prepare", error: (caught as Error).message };
          if (caught instanceof ApiError && (caught.code === "JOB_UNAVAILABLE" || (caught.code === "CONFLICT" && caught.message === "The application deadline has passed."))) {
            setUnavailable(values => ({ ...values, [job.id]: true }));
          }
        }
        write({ ...next });
      }
      if (options.automatic && !stopRef.current) await submitPrepared(next, approvedAt);
      else setNotice(stopRef.current ? "Bulk preparation stopped. Completed applications are saved." : options.automatic ? "Bulk preparation complete. Check the prepared values and explicitly approve eligible applications." : "Bulk preparation complete. View any job's filled fields and open it to edit or submit.");
    } catch (caught) {
      setError((caught as Error).message);
      setNotice("Application run stopped. Prepared applications remain saved; check their status before starting again.");
    } finally { setRunning(false); setProgress(null); }
  }, [write]);

  const submitReady = useCallback(async () => {
    await submitPrepared(resultsRef.current, Date.now());
  }, []);

  const requestStop = useCallback(() => {
    stopRef.current = true;
    setNotice("Stopping after the current job finishes.");
  }, []);

  const clear = useCallback(() => {
    write({});
    setHeldForReview(() => ({}));
    setNotice("");
    setError("");
  }, [write, setHeldForReview]);

  const acknowledgeUnavailable = useCallback((ids: string[]) => {
    setUnavailable(values => {
      const next = { ...values };
      for (const id of ids) delete next[id];
      return next;
    });
  }, []);

  return <BulkRunContext.Provider value={{ running, progress, notice, error, results, heldForReview, unavailable, acknowledgeUnavailable,
    setHeldForReview, setError, setNotice, prepare, submitReady, requestStop, clear, mergeResults, refreshResults }}>
    {children}
  </BulkRunContext.Provider>;
}

export function useBulkRun() {
  const value = useContext(BulkRunContext);
  if (!value) throw new Error("useBulkRun must be used inside BulkRunProvider.");
  return value;
}
