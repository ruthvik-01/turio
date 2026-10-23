"use client";
import Link from "next/link";
import { useEffect, useRef, useState, type Dispatch, type SetStateAction } from "react";
import { api, ApiError, requestKey, saveApplicationAnswers } from "@/lib/api";
import { approvalFingerprint, automaticBlocker, batchApprovalFresh, filledValue, sharedQuestionKey } from "@/lib/bulk";
import type { Application, Field, Job, Profile } from "@/lib/types";
import { Notice } from "./ui";
import { Select } from "./select";

type BulkResult = { job: Job; application?: Application; error?: string; stage?: "prepare" | "review" | "submit" };
export function BulkApplications({ selected, onSelect, visibleJobs, loading = false, externalBusy = false, onBusyChange,
  initialApplications, onUpdated, onUnavailable }: {
  selected: Record<string, Job>; onSelect: Dispatch<SetStateAction<Record<string, Job>>>; visibleJobs: Job[];
  loading?: boolean; externalBusy?: boolean; onBusyChange?: (busy: boolean) => void;
  initialApplications?: Application[]; onUpdated?: () => void; onUnavailable?: (id: string) => void;
}) {
  const [running, setRunning] = useState(false);
  const busy = externalBusy || running;
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  function setBusy(value: boolean) { setRunning(value); onBusyChange?.(value); }
  function removeUnavailableJob(id: string) { onUnavailable?.(id); }
  const [bulkResults, setBulkResults] = useState<Record<string, BulkResult>>({});
  const [bulkRunning, setBulkRunning] = useState(false);
  const [bulkMode, setBulkMode] = useState<"review" | "automatic">("review");
  const [bulkApproved, setBulkApproved] = useState(false);
  const [bulkAiConsent, setBulkAiConsent] = useState(false);
  const [heldForReview, setHeldForReview] = useState<Record<string, boolean>>({});
  const [sharedValues, setSharedValues] = useState<Record<string, Field["value"]>>({});
  const bulkSubmitKeys = useRef<Record<string, Record<string, string>>>({});
  const bulkKeys = useRef<Record<string, Record<string, string>>>({});
  const stopBulk = useRef(false);
  useEffect(() => {
    if (initialApplications) setBulkResults(previous => ({ ...previous,
      ...Object.fromEntries(initialApplications.map(application => [application.id,
        { job: { ...application.job, id: application.id }, application, stage: "prepare" as const }])) }));
  }, [initialApplications]);
  useEffect(() => { setBulkApproved(false); }, [selected]);
  async function prepareBulk(failedOnly = false, automatic = false) {
    if (busy) return;
    const queue = Object.values(selected).filter(job => bulkResults[job.id]?.stage !== "submit" && !["preparing", "approved_for_submission", "submitting", "submitted", "cancelled", "verification_failed"].includes(bulkResults[job.id]?.application?.status || "") && (automatic || (failedOnly ? !!bulkResults[job.id]?.error : !!initialApplications || !bulkResults[job.id]?.application || !!bulkResults[job.id]?.error)));
    const approval = automatic ? `Start automatic applications for these ${queue.length} selected jobs? I approve sending my current stored resume, profile and confirmed saved answers to eligible employers. Turio will prepare and submit them in this run. Missing answers, held jobs, unsupported forms and uncertain submissions remain pending. Approval expires after 15 minutes.` : `Allow Turio to inspect ${queue.length} employer application forms using your stored profile, resume and saved answers? Nothing will be submitted until you explicitly approve.`;
    if (!queue.length || !window.confirm(`${approval} ${bulkAiConsent ? "OpenRouter will receive employer field labels and options for this batch, not your profile values." : "AI assistance is off for this batch."}`)) return;
    const approvedAt = Date.now();
    setBulkApproved(false); setBusy(true); setBulkRunning(true); setError(""); stopBulk.current = false;
    const aiAssist = bulkAiConsent; setBulkAiConsent(false);
    const results = { ...bulkResults };
    try {
      const profileVersion = automatic ? (await api<Profile>("/profiles/me")).version : null;
      for (const [index, job] of queue.entries()) {
        if (stopBulk.current) break;
        setNotice(`Preparing ${index + 1} of ${queue.length}: ${job.company} — ${job.title}. Keep this page open.`);
        let application = results[job.id]?.application || initialApplications?.find(app => app.id === job.id);
        try {
          bulkKeys.current[job.id] ||= requestKey();
          application ||= await api<Application>("/applications", { method: "POST", headers: bulkKeys.current[job.id], body: JSON.stringify({ job_id: initialApplications?.find(app => app.id === job.id)?.job.id || job.id, reuse_existing: true }) });
          application = await api<Application>(`/applications/${application.id}`);
          if (["created", "automation_failed"].includes(application.status) || ((application.manual_submission_required || (automatic && application.profile_version !== profileVersion)) && ["needs_input", "ready_for_review"].includes(application.status))) {
            const capability = await api<{ available: boolean; reason: string | null }>(`/applications/${application.id}/capability`);
            if (!capability.available) throw new Error(capability.reason || "Agent preparation is unavailable for this job.");
            application = await api<Application>(`/applications/${application.id}/start`, { method: "POST", body: JSON.stringify({ ai_assist: aiAssist }) });
          }
          results[job.id] = { job, application, stage: "prepare" };
        } catch (error) {
          results[job.id] = { job, application, stage: "prepare", error: (error as Error).message };
          if (error instanceof ApiError && (error.code === "JOB_UNAVAILABLE" || (error.code === "CONFLICT" && error.message === "The application deadline has passed."))) removeUnavailableJob(job.id);
        }
        setBulkResults({ ...results });
      }
      if (automatic && !stopBulk.current) await submitPrepared(results, approvedAt);
      else setNotice(stopBulk.current ? "Bulk preparation stopped. Completed applications are saved; continue with the remaining selection." : bulkMode === "automatic" ? "Bulk preparation complete. Check the prepared values below and explicitly approve eligible applications. No submissions yet." : "Bulk preparation complete. View any job's filled fields and open it to edit or submit. No automatic submissions.");
    } catch (error) {
      setError((error as Error).message);
      setNotice("Application run stopped. Prepared applications remain saved; check their status before starting again.");
    } finally { setBusy(false); setBulkRunning(false); onUpdated?.(); }
  }
  async function submitBulk() {
    if (busy || bulkMode !== "automatic" || !bulkApproved || !automaticQueue.length) return;
    await submitPrepared(bulkResults, Date.now());
  }
  async function submitPrepared(prepared: Record<string, BulkResult>, approvedAt: number) {
    const queue = Object.values(prepared).filter(result => selected[result.job.id] && result.application && !result.error && !heldForReview[result.job.id] && automaticBlocker(result.application) === null)
      .map(result => ({ ...result, fingerprint: approvalFingerprint(result.application!) }));
    const results = { ...prepared };
    let approvalExpired = false;
    setBulkApproved(false); setBusy(true); setBulkRunning(true); setError(""); stopBulk.current = false;
    try {
      for (const [index, result] of queue.entries()) {
        if (stopBulk.current) break;
        if (!batchApprovalFresh(approvedAt)) { approvalExpired = true; break; }
        let application = result.application!;
        let stage: "review" | "submit" = "review";
        setNotice(`Submitting ${index + 1} of ${queue.length}: ${result.job.company} — ${result.job.title}. Keep this page open.`);
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
          bulkSubmitKeys.current[key] ||= requestKey();
          stage = "submit";
          application = await api<Application>(`/applications/${application.id}/approve-submit`, { method: "POST", headers: bulkSubmitKeys.current[key], body: JSON.stringify({ approved: true, review_token: token }) });
          if (application.status === "verification_failed" && application.events.some(event=>event.event_type === "verification_failed" && event.event_data.error_code === "JOB_UNAVAILABLE")) removeUnavailableJob(result.job.id);
          results[result.job.id] = { job: result.job, application, stage };
        } catch (error) {
          if (error instanceof ApiError && error.code === "JOB_UNAVAILABLE") removeUnavailableJob(result.job.id);
          if (stage === "submit") {
            try { application = await api<Application>(`/applications/${application.id}`); } catch { /* Check manually; never replay a submission. */ }
          }
          results[result.job.id] = { job: result.job, application, stage,
            error: application.status === "submitted" ? undefined : `${(error as Error).message}${stage === "submit" ? " Check status in the application; no automatic retry." : ""}` };
        }
        setBulkResults({ ...results });
      }
      setNotice(approvalExpired ? "Bulk approval expired. Approve the remaining applications again." : stopBulk.current ? "Stopped after the current job. Other applications remain pending." : "Automatic batch finished. Confirmed ready applications were submitted; missing answers, held and unsupported jobs remain pending. Answer shared questions below once, then start automatic applications again.");
    } finally { setBusy(false); setBulkRunning(false); onUpdated?.(); }
  }
  const selectedResults = Object.values(bulkResults).filter(result => selected[result.job.id]);
  const automaticQueue = selectedResults.filter(result => result.application && !result.error && !heldForReview[result.job.id] && automaticBlocker(result.application) === null);
  const sharedQuestions = new Map<string, { field: Field; application: Application; count: number }>();
  for (const result of selectedResults) {
    const application = result.application;
    if (!application || !["needs_input", "ready_for_review"].includes(application.status)) continue;
    for (const field of application.fields) {
      const key = sharedQuestionKey(field);
      if (!key || !field.required || ["profile", "jev_profile", "application_only"].includes(field.value_source)
          || (field.user_confirmed && field.value !== null && field.value !== "" && (!Array.isArray(field.value) || field.value.length))) continue;
      const previous = sharedQuestions.get(key);
      sharedQuestions.set(key, previous ? { ...previous, count: previous.count + 1 } : { field, application, count: 1 });
    }
  }
  async function saveSharedAnswers() {
    setBusy(true); setError(""); setBulkApproved(false);
    try {
      for (const [key, question] of sharedQuestions) {
        const value = sharedValues[key];
        if (value === undefined || value === null || value === "" || (Array.isArray(value) && !value.length)) continue;
        await saveApplicationAnswers(question.application, [{ field_id: question.field.id, value, user_confirmed: true, save_for_reuse: true }]);
      }
      const results = { ...bulkResults };
      for (const result of selectedResults) if (result.application) {
        const application = await api<Application>(`/applications/${result.application.id}`);
        results[result.job.id] = { ...result, application, error: result.stage === "submit" ? result.error : undefined };
      }
      setBulkResults(results); onUpdated?.(); setSharedValues({}); setNotice("Shared answers saved across matching pending applications. Start automatic applications to send ready jobs.");
    } catch (error) { setError((error as Error).message); } finally { setBusy(false); }
  }
  return <>{error && <Notice kind="error">{error}</Notice>}{notice && <Notice>{notice}</Notice>}
<section className="panel detail-panel minimal-bulk-panel" style={{ marginBottom: 24 }}>
      <div className="section-header-row">
        <h2>Bulk applications</h2>
        <span className="small muted">{Object.keys(selected).length} selected</span>
      </div>
      <p className="small muted" style={{ margin: "4px 0 10px" }}>Prepare and send multiple applications using your saved profile.</p>
      <details className="more" style={{ marginBottom: 16 }}>
        <summary>How it works</summary>
        <p className="small muted" style={{ marginTop: 6, lineHeight: 1.6 }}>
          Automatic submission prepares and sends selected jobs using your stored resume, profile and confirmed answers.
          You approve before anything is submitted. Missing answers are asked once; unsupported forms remain pending.
        </p>
      </details>
      <label>Bulk application mode<Select label="Bulk application mode" value={bulkMode} disabled={busy} onChange={value => { setBulkMode(value as "review" | "automatic"); setBulkApproved(false); }} options={[{ value: "review", label: "Fill & review" }, { value: "automatic", label: "Automatic submission" }]} /></label>
      <label className="check-label small" style={{ marginTop: 12 }}><input type="checkbox" checked={bulkAiConsent} disabled={busy} onChange={e => setBulkAiConsent(e.target.checked)} />Use AI for unfamiliar employer fields in this batch. I agree to send field labels/options through OpenRouter; profile values stay local.</label>
      <div className="actions" style={{ marginTop: 16 }}><button className="button secondary small" disabled={busy || loading || !visibleJobs.length} onClick={() => { setBulkApproved(false); onSelect(values => ({ ...values, ...Object.fromEntries(visibleJobs.map(job => [job.id, job])) })); }}>Select visible jobs</button><button className="button primary" disabled={busy || !Object.keys(selected).length} onClick={() => void prepareBulk(false, bulkMode === "automatic")}>{bulkMode === "automatic" ? "Start automatic applications" : "Prepare selected applications"}</button>{selectedResults.some(result => result.error && result.stage !== "submit") && <button className="button secondary small" disabled={busy} onClick={() => void prepareBulk(true, bulkMode === "automatic")}>Retry failed applications</button>}{bulkRunning ? <button className="text-button" onClick={() => { stopBulk.current = true; setNotice("Stopping after the current job finishes."); }}>Stop after current job</button> : <button className="text-button" disabled={busy || !Object.keys(selected).length} onClick={() => { onSelect({}); setBulkResults({}); setHeldForReview({}); setBulkApproved(false); setSharedValues({}); }}>Clear selection</button>}<span className="small muted" aria-live="polite">{Object.keys(selected).length} selected</span></div>
      {!!sharedQuestions.size && <div className="review-box"><h3>Answer once for selected applications</h3><p className="small muted">Saving a confirmed answer updates matching questions in your pending applications. Different questions and application-specific answers stay separate.</p>
        {Array.from(sharedQuestions, ([key, { field, count }]) => <label key={key} style={{ marginTop: 16 }}>{field.label} * <span className="small muted">({count} pending {count === 1 ? "field" : "fields"})</span>
          {field.input_type === "select" || field.input_type === "multiselect" ? (field.input_type === "multiselect"
            ? <Select multiple disabled={busy} value={sharedValues[key] as string[] || []} onChange={value => setSharedValues(values => ({ ...values, [key]: value }))} options={field.options} />
            : <Select disabled={busy} value={String(sharedValues[key] ?? "")} onChange={value => setSharedValues(values => ({ ...values, [key]: value }))} options={field.options} />)
          : field.input_type === "textarea" ? <textarea disabled={busy} maxLength={10000} value={String(sharedValues[key] ?? "")} onChange={e => setSharedValues(values => ({ ...values, [key]: e.target.value }))} />
          : <input disabled={busy} type={["email", "tel", "url", "number"].includes(field.input_type) ? field.input_type : "text"} maxLength={10000} value={String(sharedValues[key] ?? "")} onChange={e => setSharedValues(values => ({ ...values, [key]: e.target.value }))} />}
          {field.help_text && <span className="small muted">{field.help_text}</span>}
        </label>)}
        <button className="button secondary" style={{ marginTop: 16 }} disabled={busy || !Object.values(sharedValues).some(value => value !== null && value !== "" && (!Array.isArray(value) || !!value.length))} onClick={() => void saveSharedAnswers()}>Save shared answers</button>
      </div>}
      {selectedResults.map(result => <div className="review-box" key={result.job.id}><p>{result.job.company} · {result.job.title}</p>{result.error ? <p className="small" role="alert">{result.error}</p> : <p className="small muted">{result.application?.status.replaceAll("_", " ")}{result.application?.missing_fields.length ? ` · ${result.application.missing_fields.length} required answers needed` : ""}</p>}
        {result.application && <><details className="answer-summary"><summary>View filled fields for {result.job.title} at {result.job.company}</summary><dl>{result.application.fields.map(field => <div key={field.id}><dt>{field.label}</dt><dd>{filledValue(field)}{!field.user_confirmed && <span className="small muted"> · not confirmed</span>}{field.help_text && <p className="small muted">{field.help_text}</p>}</dd></div>)}</dl></details><Link className="inline-link" href={`/applications/${result.application.id}`}>Open application</Link>
          {bulkMode === "automatic" && <><label className="check-label small" style={{ marginTop: 12 }}><input type="checkbox" checked={!!heldForReview[result.job.id]} disabled={busy} onChange={e => { setHeldForReview(values => ({ ...values, [result.job.id]: e.target.checked })); setBulkApproved(false); }} />Hold {result.job.title} at {result.job.company} for review</label><p className="small muted">{heldForReview[result.job.id] ? "Held for your review; excluded from automatic submission." : automaticBlocker(result.application) || "Eligible for batch approval."}</p></>}
        </>}
      </div>)}
      {bulkMode === "automatic" && selectedResults.length > 0 && <div className="review-box"><p>{automaticQueue.length} ready applications. Start automatic applications prepares and submits confirmed ready jobs with your run approval. Jobs missing answers stay pending. You can also review these prepared values and approve just the ready applications below. Approval lasts 15 minutes; changed answers require new approval.</p><label className="check-label"><input type="checkbox" checked={bulkApproved} disabled={busy || !automaticQueue.length} onChange={e => setBulkApproved(e.target.checked)} />I explicitly approve submitting the eligible applications shown above with these prepared answers and my stored resume.</label><button className="button primary" style={{ marginTop: 12 }} disabled={busy || !bulkApproved || !automaticQueue.length} onClick={() => void submitBulk()}>Approve & submit ready applications</button></div>}
    </section>
  </>;
}
