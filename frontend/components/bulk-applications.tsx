"use client";
import Link from "next/link";
import { useEffect, useState, type Dispatch, type SetStateAction } from "react";
import { saveApplicationAnswers } from "@/lib/api";
import { automaticBlocker, filledValue, sharedQuestionKey } from "@/lib/bulk";
import type { Application, Field, Job } from "@/lib/types";
import { Notice } from "./ui";
import { Select } from "./select";
import { useBulkRun } from "./bulk-run";

export function BulkApplications({ selected, onSelect, visibleJobs, loading = false, externalBusy = false, onBusyChange,
  initialApplications, onUpdated }: {
  selected: Record<string, Job>; onSelect: Dispatch<SetStateAction<Record<string, Job>>>; visibleJobs: Job[];
  loading?: boolean; externalBusy?: boolean; onBusyChange?: (busy: boolean) => void;
  initialApplications?: Application[]; onUpdated?: () => void;
}) {
  const run = useBulkRun();
  const busy = externalBusy || run.running;
  const [bulkMode, setBulkMode] = useState<"review" | "automatic">("review");
  const [bulkApproved, setBulkApproved] = useState(false);
  const [bulkAiConsent, setBulkAiConsent] = useState(false);
  const [sharedValues, setSharedValues] = useState<Record<string, Field["value"]>>({});
  useEffect(() => { onBusyChange?.(run.running); }, [run.running, onBusyChange]);
  useEffect(() => { if (initialApplications) run.mergeResults(initialApplications); }, [initialApplications, run.mergeResults]);
  useEffect(() => { setBulkApproved(false); }, [selected]);
  async function prepareBulk(failedOnly = false, automatic = false) {
    if (busy) return;
    const queue = Object.values(selected).filter(job => run.results[job.id]?.stage !== "submit" && !["preparing", "approved_for_submission", "submitting", "submitted", "cancelled", "verification_failed"].includes(run.results[job.id]?.application?.status || "") && (automatic || (failedOnly ? !!run.results[job.id]?.error : !!initialApplications || !run.results[job.id]?.application || !!run.results[job.id]?.error)));
    const approval = automatic ? `Start automatic applications for these ${queue.length} selected jobs? I approve sending my current stored resume, profile and confirmed saved answers to eligible employers. Turio will prepare and submit them in this run. Missing answers, held jobs, unsupported forms and uncertain submissions remain pending. Approval expires after 15 minutes.` : `Allow Turio to inspect ${queue.length} employer application forms using your stored profile, resume and saved answers? Nothing will be submitted until you explicitly approve.`;
    if (!queue.length || !window.confirm(`${approval} ${bulkAiConsent ? "OpenRouter will receive employer field labels and options for this batch, not your profile values." : "AI assistance is off for this batch."}`)) return;
    const aiConsent = bulkAiConsent; setBulkAiConsent(false); setBulkApproved(false);
    await run.prepare(queue, { automatic, aiConsent });
    onUpdated?.();
  }
  async function submitBulk() {
    if (busy || bulkMode !== "automatic" || !bulkApproved || !automaticQueue.length) return;
    setBulkApproved(false);
    await run.submitReady();
    onUpdated?.();
  }
  // Results live in the provider and outlive this page, so show every prepared job,
  // not just the ones selected on the page the user happens to be on.
  const selectedResults = Object.values(run.results);
  const automaticQueue = selectedResults.filter(result => result.application && !result.error && !run.heldForReview[result.job.id] && automaticBlocker(result.application) === null);
  const sharedQuestions = new Map<string, { field: Field; application: Application; count: number }>();
  for (const result of selectedResults) {
    const application = result.application;
    if (!application || !["needs_input", "ready_for_review"].includes(application.status)) continue;
    for (const field of application.fields) {
      const key = sharedQuestionKey(field);
      if (!key || !field.required || ["profile", "ai_profile", "application_only"].includes(field.value_source)
          || (field.user_confirmed && field.value !== null && field.value !== "" && (!Array.isArray(field.value) || field.value.length))) continue;
      const previous = sharedQuestions.get(key);
      sharedQuestions.set(key, previous ? { ...previous, count: previous.count + 1 } : { field, application, count: 1 });
    }
  }
  async function saveSharedAnswers() {
    setBulkApproved(false); run.setError("");
    try {
      for (const [key, question] of sharedQuestions) {
        const value = sharedValues[key];
        if (value === undefined || value === null || value === "" || (Array.isArray(value) && !value.length)) continue;
        await saveApplicationAnswers(question.application, [{ field_id: question.field.id, value, user_confirmed: true, save_for_reuse: true }]);
      }
      await run.refreshResults(selectedResults.map(result => result.job.id));
      onUpdated?.(); setSharedValues({}); run.setNotice("Shared answers saved across matching pending applications.");
    } catch (caught) { run.setError((caught as Error).message); }
  }
  return <>{run.error && <Notice kind="error">{run.error}</Notice>}{run.notice && <Notice>{run.notice}</Notice>}
<section className={`panel detail-panel minimal-bulk-panel${run.running ? " bulk-active" : ""}`} style={{ marginBottom: 24 }}>
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
      <div className="actions" style={{ marginTop: 16 }}><button className="button secondary small" disabled={busy || loading || !visibleJobs.length} onClick={() => { setBulkApproved(false); onSelect(values => ({ ...values, ...Object.fromEntries(visibleJobs.map(job => [job.id, job])) })); }}>Select visible jobs</button><button className="button primary" disabled={busy || !Object.keys(selected).length} onClick={() => void prepareBulk(false, bulkMode === "automatic")}>{bulkMode === "automatic" ? "Start automatic applications" : "Prepare selected applications"}</button>{selectedResults.some(result => result.error && result.stage !== "submit") && <button className="button secondary small" disabled={busy} onClick={() => void prepareBulk(true, bulkMode === "automatic")}>Retry failed applications</button>}{run.running ? <button className="text-button" onClick={run.requestStop}>Stop after current job</button> : <button className="text-button" disabled={busy || !Object.keys(selected).length} onClick={() => { onSelect({}); run.clear(); setBulkApproved(false); setSharedValues({}); }}>Clear selection</button>}<span className="small muted" aria-live="polite">{Object.keys(selected).length} selected</span></div>
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
      {selectedResults.map(result => <div className={`review-box${run.running ? " bulk-active" : ""}`} key={result.job.id}><p>{result.job.company} · {result.job.title}</p>{result.error ? <p className="small" role="alert">{result.error}</p> : <p className="small muted">{result.application?.status.replaceAll("_", " ")}{result.application?.missing_fields.length ? ` · ${result.application.missing_fields.length} required answers needed` : ""}</p>}
        {result.application && <><details className="answer-summary"><summary>View filled fields for {result.job.title} at {result.job.company}</summary><dl>{result.application.fields.map(field => <div className="answer-row" key={field.id}><dt>{field.label}</dt><dd title={filledValue(field)}>{filledValue(field)}{!field.user_confirmed && <span className="small muted"> · not confirmed</span>}</dd>{field.help_text && <span className="help">{field.help_text}</span>}</div>)}</dl></details><Link className="inline-link" href={`/applications/${result.application.id}`}>Open application</Link>
          {bulkMode === "automatic" && <><label className="check-label small" style={{ marginTop: 12 }}><input type="checkbox" checked={!!run.heldForReview[result.job.id]} disabled={busy} onChange={e => { run.setHeldForReview(values => ({ ...values, [result.job.id]: e.target.checked })); setBulkApproved(false); }} />Hold {result.job.title} at {result.job.company} for review</label><p className="small muted">{run.heldForReview[result.job.id] ? "Held for your review; excluded from automatic submission." : automaticBlocker(result.application) || "Eligible for batch approval."}</p></>}
        </>}
      </div>)}
      {bulkMode === "automatic" && selectedResults.length > 0 && <div className="review-box"><p>{automaticQueue.length} ready applications. Start automatic applications prepares and submits confirmed ready jobs with your run approval. Jobs missing answers stay pending. You can also review these prepared values and approve just the ready applications below. Approval lasts 15 minutes; changed answers require new approval.</p><label className="check-label"><input type="checkbox" checked={bulkApproved} disabled={busy || !automaticQueue.length} onChange={e => setBulkApproved(e.target.checked)} />I explicitly approve submitting the eligible applications shown above with these prepared answers and my stored resume.</label><button className="button primary" style={{ marginTop: 12 }} disabled={busy || !bulkApproved || !automaticQueue.length} onClick={() => void submitBulk()}>Approve & submit ready applications</button></div>}
    </section>
  </>;
}
