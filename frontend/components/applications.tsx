"use client";
import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, requestKey, safeExternalUrl, saveApplicationAnswers, type ApplicationAnswerInput } from "@/lib/api";
import { filledValue, sharedQuestionKey } from "@/lib/bulk";
import type { Application, ApplicationPage, Field, Job } from "@/lib/types";
import { useSession } from "./session";
import { CompanyLogo, Empty, Loading, Notice, PageHeading, Pagination, Status, Workspace } from "./ui";
import { Select } from "./select";

import { BulkApplications } from "./bulk-applications";

const outcomes = ["under_review", "interview", "offer", "rejected", "withdrawn", "accepted"];
const statuses = ["created", "preparing", "needs_input", "ready_for_review", "submitting", "submitted", "verification_failed", "automation_failed", "cancelled"];
function answered(field: Field) {
  return field.user_confirmed && field.value !== null && (typeof field.value !== "string" || !!field.value.trim())
    && (!Array.isArray(field.value) || field.value.length > 0)
    && !(field.required && field.input_type === "checkbox" && field.value !== true);
}
export function Applications({ initialOutcome = "", interviews = false }: { initialOutcome?: string; interviews?: boolean }) {
  const { user } = useSession(); const [data, setData] = useState<ApplicationPage | null>(null);
  const [outcome, setOutcome] = useState(interviews ? "interview" : initialOutcome); const [status, setStatus] = useState("");
  const [selected, setSelected] = useState<Record<string, Job>>({});
  const [bulkBusy, setBulkBusy] = useState(false); const [version, setVersion] = useState(0);
  const bulkApps = data?.applications.filter(app => !["preparing", "approved_for_submission", "submitting", "submitted", "cancelled", "verification_failed"].includes(app.status)) ?? [];
  const visibleJobs = bulkApps.map(app => ({ ...app.job, id: app.id }));
  const [offset, setOffset] = useState(0); const [error, setError] = useState(""); const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!user) return;
    let active = true; setLoading(true); setError("");
    api<ApplicationPage>(`/applications?limit=12&offset=${offset}${status ? `&status=${status}` : ""}${outcome ? `&outcome=${outcome}` : ""}`)
      .then(value => { if (active) setData(value); }).catch(error => { if (active) setError(error.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [user, offset, status, outcome, version]);
  return <Workspace><PageHeading eyebrow="" title={interviews ? "Interviews" : "Applications"} action={<Link className="button primary" href="/jobs">Browse jobs</Link>}>{interviews ? "View applications marked for interview and keep follow-up notes." : "Review your applications and update their status or outcome."}</PageHeading>
    <div className="filters panel"><label>Application status<Select label="Application status" value={status} onChange={value => { setStatus(value); setOffset(0); }} placeholder="All statuses" options={[{ value: "", label: "All statuses" }, ...statuses.map(s => ({ value: s, label: s.replaceAll("_", " ") }))]} /></label>{!interviews && <label>Outcome<Select label="Outcome" value={outcome} onChange={value => { setOutcome(value); setOffset(0); }} placeholder="All outcomes" options={[{ value: "", label: "All outcomes" }, ...outcomes.map(s => ({ value: s, label: s.replaceAll("_", " ") }))]} /></label>}</div>
    {!interviews && <BulkApplications selected={selected} onSelect={setSelected} visibleJobs={visibleJobs} loading={loading}
      onBusyChange={setBulkBusy} initialApplications={data?.applications} onUpdated={() => setVersion(value => value + 1)} />}
    {error && <Notice kind="error">{error}</Notice>}{loading ? <Loading /> : data && (data.applications.length ? <><div className="panel table-wrap"><table className="data-table"><thead><tr>{!interviews && <th scope="col">Select</th>}<th scope="col">Opportunity</th><th scope="col">Status</th><th scope="col">Outcome</th><th scope="col">Started</th><th scope="col"><span className="small">Review</span></th></tr></thead><tbody>{data.applications.map(app => <tr key={app.id}>{!interviews && <td><label className="check-label"><input type="checkbox" aria-label={`Select ${app.job.title} at ${app.job.company}`} checked={!!selected[app.id]}
      disabled={bulkBusy || !bulkApps.some(item => item.id === app.id)} onChange={e => setSelected(values => { const next = { ...values }; if (e.target.checked) next[app.id] = { ...app.job, id: app.id }; else delete next[app.id]; return next; })} /></label></td>}<td><Link className="table-job" href={`/applications/${app.id}`}><CompanyLogo job={app.job} /><span><strong>{app.job.title}</strong><br /><span className="muted small">{app.job.company}</span></span></Link></td><td><Status value={app.status} /></td><td>{app.outcome?.replaceAll("_", " ") || "Not recorded"}</td><td>{new Date(app.created_at).toLocaleDateString()}</td><td><Link className="inline-link" aria-label={`Review ${app.job.title}`} href={`/applications/${app.id}`}>↗</Link></td></tr>)}</tbody></table></div><Pagination total={data.total} offset={offset} onChange={setOffset} /></> :
      <Empty title={interviews ? "No interviews recorded" : "No applications found"} action={<Link href="/jobs" className="button secondary">Explore jobs</Link>}>{interviews ? "Applications marked with the interview outcome will appear here. Record dates and follow-ups in the application's notes." : "No applications match these filters. Start from a job posting to prepare and track an application."}</Empty>)}
  </Workspace>;
}

export function ApplicationDetail({ applicationId, reviewMode = false }: { applicationId: string; reviewMode?: boolean }) {
  const { user } = useSession();
  const [app, setApp] = useState<Application | null>(null); const [fields, setFields] = useState<Field[]>([]);
  const [showFilled, setShowFilled] = useState(false); const [notes, setNotes] = useState(""); const [outcome, setOutcome] = useState("");
  const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [notice, setNotice] = useState("");
  const [approved, setApproved] = useState(false); const [manual, setManual] = useState(false); const [dirty, setDirty] = useState(false);
  const [capability, setCapability] = useState<{ available: boolean; reason: string | null } | null>(null);
  const [aiConsent, setAiConsent] = useState(false);
  const [reuse, setReuse] = useState<Record<string, boolean>>({});
  const [notSubmitted, setNotSubmitted] = useState(false);
  const [nowMs, setNowMs] = useState(() => Date.now());
  const [jevConfirmed, setJevConfirmed] = useState<Record<string, boolean>>({});
  const approvalKey = useRef<Record<string, string> | null>(null);
  const prefix = `/applications/${applicationId}`;
  function populate(value: Application) { setApp(value); setFields(value.fields); setNotes(value.notes || ""); setOutcome(value.outcome || ""); setDirty(false); setApproved(false); setShowFilled(false); setJevConfirmed({}); setReuse({}); setNotSubmitted(false); approvalKey.current = null; }
  useEffect(() => { if (user) api<Application>(prefix).then(populate).catch(error => setError(error.message)); }, [user, prefix]);
  useEffect(() => {
    if (!app?.reviewed_at || app.status !== "ready_for_review") return;
    setNowMs(Date.now());
    const id = window.setInterval(() => setNowMs(Date.now()), 15000);
    return () => window.clearInterval(id);
  }, [app?.reviewed_at, app?.status]);
  useEffect(() => {
    if (!user) return;
    let active = true;
    setCapability(null);
    api<{ available: boolean; reason: string | null }>(`${prefix}/capability`)
      .then(value => { if (active) setCapability(value); })
      .catch(() => { if (active) setCapability({ available: false, reason: "Browser availability could not be checked. Reload to retry, or continue on the employer site." }); });
    return () => { active = false; };
  }, [user, prefix]);
  async function act(path: string, payload?: object, method = "POST", headers?: Record<string, string>) {
    setBusy(true); setError(""); setNotice("");
    try {
      const result = path === "/answers" && app
        ? await saveApplicationAnswers(app, (payload as { answers: ApplicationAnswerInput[] }).answers, headers)
        : await api<Application>(prefix + path, { method, headers, body: payload ? JSON.stringify(payload) : undefined }); populate(result); if (path === "/handoff") { const message = String(result.events.at(-1)?.event_data.message || "Browser handoff updated."); if (result.status === "automation_failed") setError(message); else setNotice(message); } else setNotice("Application updated.");
    }
    catch (error) { setError((error as Error).message); } finally { setBusy(false); }
  }
  function change(id: string, value: Field["value"]) {
    setFields(items => {
      const current = items.find(f => f.id === id)!;
      const key = sharedQuestionKey(current);
      return items.map(f => f.id === id || (key && !["profile", "application_only"].includes(current.value_source) && reuse[id] !== false && sharedQuestionKey(f) === key && !["profile", "jev_profile", "application_only"].includes(f.value_source))
        ? { ...f, value, user_confirmed: f.value_source !== "jev_profile" } : f);
    }); setReuse(values => ({ ...values, [id]: values[id] ?? !["profile", "application_only"].includes(fields.find(f => f.id === id)!.value_source) })); setJevConfirmed(values => ({ ...values, [id]: false })); setDirty(true); setApproved(false);
  }
  async function prepare() {
    if (!window.confirm("Allow Turio to open this employer's application form and prepare it using your saved profile and resume? You will review the answers before filling. Nothing will be submitted without your separate final approval.")) return;
    const consent = aiConsent; setAiConsent(false); await act("/start", { ai_assist: consent });
  }
  async function saveAnswers(event: FormEvent) {
    event.preventDefault();
    await act("/answers", { answers: visibleFields.filter(f => f.input_type !== "file" && (f.value_source !== "profile" || reuse[f.id] !== undefined || app?.fields.find(original => original.id === f.id)?.value !== f.value)).map(f => ({ field_id: f.id, value: f.value, user_confirmed: f.user_confirmed, jev_confirmed: !!jevConfirmed[f.id], save_for_reuse: f.value_source !== "jev_profile" && (reuse[f.id] ?? !["profile", "application_only"].includes(f.value_source)) })) }, "POST", requestKey());
  }
  const locked = busy || !!app && ["preparing", "approved_for_submission", "submitting", "submitted", "cancelled", "verification_failed"].includes(app.status);
  const filledFields = app?.fields.filter(answered) ?? [];
  const reviewRemainingMs = app?.reviewed_at ? Math.max(0, new Date(app.reviewed_at).getTime() + 15 * 60 * 1000 - nowMs) : null;
  const reviewExpired = reviewRemainingMs !== null && reviewRemainingMs <= 0;
  const visibleFields = fields.filter(field => showFilled ? field.input_type !== "file" : field.required && !filledFields.some(f => f.id === field.id));
  return <Workspace><Link className="inline-link" href="/applications">← All applications</Link>{error && <Notice kind="error">{error}</Notice>}{notice && <Notice kind="success">{notice}</Notice>}{!app ? !error && <Loading /> : <>
    <div style={{ marginTop: 28 }}><PageHeading eyebrow={app.job.company} title={reviewMode ? "Review application" : app.job.title} action={<Status value={app.status} />}>Check your answers before preparing the final review.</PageHeading></div>
    <div className="two-column"><div><section className="panel detail-panel"><h2>Application preparation</h2><p className="small muted">Optional AI assistance sends field labels, control types and options to an external AI service for this action. Your profile values stay local. The service may retain this metadata under its terms.</p><label className="check-label"><input type="checkbox" checked={aiConsent} disabled={locked} onChange={e => setAiConsent(e.target.checked)} />Use AI to suggest unfamiliar field mappings for this action.</label><p className="muted" role="status">{!capability ? "Checking browser availability…" : capability.available ? "Browser assistant ready. Starting requires your permission; the form will be checked before filling." : capability.reason}</p>
      <p className="small muted">{app.resume_id ? "Your stored resume and profile will be reused. No per-job upload is needed." : <>No resume selected yet. <Link className="inline-link" href="/profile">Upload a PDF in your profile</Link>, then return here.</>} The agent prepares fields only; you must review and explicitly approve before submission.</p><div className="actions" style={{ marginTop: 20 }}><a className="button secondary" href={safeExternalUrl(app.application_url)} target="_blank" rel="noopener noreferrer">Open employer application ↗</a><button className="button primary" disabled={locked || !capability?.available} onClick={prepare}>{busy ? "Working…" : "Apply with Agent"}</button><button className="text-button" disabled={busy} onClick={() => act("/recover")}>Check status</button></div>
      {app.fields.length > 0 && <><h3>Required-field readiness · {Math.round(app.readiness_score * 100)}%</h3><div className="progress-track"><span style={{ width: `${app.readiness_score * 100}%` }} /></div><p className="small muted">This measures confirmed required fields, not hiring likelihood or live submission success.</p></>}
      {app.status === "verification_failed" && <Notice kind="error">The submission outcome is uncertain. Check the employer site before any manual retry. Automatic resubmission is disabled.</Notice>}
      {app.status === "verification_failed" && <div className="review-box"><label className="check-label"><input type="checkbox" checked={notSubmitted} disabled={busy} onChange={e => setNotSubmitted(e.target.checked)} />I checked the employer site and confirmed this application was not submitted.</label><button type="button" className="button secondary" disabled={busy || !notSubmitted} onClick={() => act("", { reset_to_review: true, confirmed_not_submitted: true }, "PATCH")}>Reset to review</button><p className="small muted">Resetting clears prior approval. Prepare a fresh review before another submission.</p></div>}
    </section>
      {app.fields.length > 0 && <section className="panel detail-panel" style={{ marginTop: 24 }}><h2>{visibleFields.length ? "Missing information" : "Your answers are ready"}</h2><p className="small muted" style={{ marginBottom: 22 }}>Your resume, profile and saved answers are reused automatically. New answers are saved for future applications. Only required questions need your attention; unanswered optional fields are skipped.</p>
        {filledFields.length > 0 && <details className="answer-summary" style={{ marginBottom: 22 }}><summary>View filled answers ({filledFields.length})</summary><dl>{filledFields.map(field => <div key={field.id}><dt>{field.label}</dt><dd>{field.input_type === "file" ? "Your stored original resume is selected." : filledValue(field)}{field.help_text && <p className="small muted">{field.help_text}</p>}</dd></div>)}</dl><div className="actions"><Link className="inline-link" href="/profile">Edit profile</Link>{filledFields.some(f => f.input_type !== "file") && <button type="button" className="text-button" disabled={locked} onClick={() => setShowFilled(value => !value)}>{showFilled ? "Hide filled fields" : "Edit filled answers"}</button>}</div></details>}
        <form onSubmit={saveAnswers}>
          {visibleFields.map(field => <div className="field-row" key={field.id}><label>{field.label}{field.required ? " *" : " (optional)"}
            {field.input_type === "file" ? <span className="muted small">{field.value ? "Your stored original resume is selected." : "No resume selected. Upload one in your profile, then use Apply with Agent again."}</span> :
              field.input_type === "checkbox" ? <input type="checkbox" checked={field.value === true} disabled={locked} onChange={e => change(field.id, e.target.checked)} /> :
                field.input_type === "multiselect" ? <Select multiple describedBy={field.help_text ? `field-help-${field.id}` : undefined} value={Array.isArray(field.value) ? field.value : []} disabled={locked} onChange={value => change(field.id, value)} options={field.options} /> :
                  field.input_type === "select" ? <Select describedBy={field.help_text ? `field-help-${field.id}` : undefined} value={String(field.value ?? "")} disabled={locked} onChange={value => change(field.id, value || null)} options={field.options} /> :
                    field.input_type === "textarea" ? <textarea aria-describedby={field.help_text ? `field-help-${field.id}` : undefined} maxLength={10000} value={String(field.value ?? "")} disabled={locked} onChange={e => change(field.id, e.target.value || null)} /> :
                      <input aria-describedby={field.help_text ? `field-help-${field.id}` : undefined} type={["email", "tel", "url", "number"].includes(field.input_type) ? field.input_type : "text"} maxLength={10000} value={String(field.value ?? "")} disabled={locked} onChange={e => change(field.id, e.target.value || null)} />}</label>
            {field.input_type !== "file" && field.value_source !== "jev_profile" && <label className="check-label small"><input type="checkbox" disabled={locked} checked={reuse[field.id] ?? !["profile", "application_only"].includes(field.value_source)} onChange={e => { setReuse(values => ({ ...values, [field.id]: e.target.checked })); setDirty(true); setApproved(false); }} />Save for future applications and update matching profile contact details.</label>}
            {field.help_text && <p className="small muted" id={`field-help-${field.id}`}>{field.help_text}</p>}
            <p className="small muted">{field.value_source === "profile" ? "From your stored profile" : field.value_source === "jev_profile" ? "AI suggestion from your profile. Editing clears confirmation; explicitly confirm before use." : field.value_source === "draft" ? "Factual starter from your profile — review and confirm before using." : field.user_confirmed ? "Confirmed answer" : "Needs your confirmation"}</p>
            {field.value_source === "jev_profile" && <p className="small muted">{field.jev_uncertain ? "Uncertain mapping — check this value carefully. " : ""}{field.jev_confidence != null ? <>Decision confidence {(field.jev_confidence * 100).toFixed(0)}%{field.jev_winner_probability != null && <>; winner probability {(field.jev_winner_probability * 100).toFixed(0)}%</>}. These are not measured accuracy.</> : "Confidence/probability scores are unavailable; verify this mapping before confirming."}</p>}
            {field.input_type === "textarea" && field.normalized_intent === "custom" && <button type="button" className="button secondary small" style={{ marginTop: 12 }} disabled={locked || dirty} onClick={() => act(`/fields/${field.id}/draft`)}>Draft from profile</button>}
            {["jev_profile", "draft"].includes(field.value_source) && <label className="check-label"><input type="checkbox" checked={field.user_confirmed} disabled={locked} onChange={e => { setFields(items => items.map(f => f.id === field.id ? { ...f, user_confirmed: e.target.checked } : f)); setJevConfirmed(values => ({ ...values, [field.id]: field.value_source === "jev_profile" && e.target.checked })); setDirty(true); setApproved(false); }} />{field.value_source === "jev_profile" ? "I explicitly confirm this AI suggestion is accurate." : "I confirm this answer is accurate."}</label>}</div>)}
          {visibleFields.some(f => f.input_type !== "file") && <button className="button secondary" disabled={locked || !dirty}>Save answers</button>}
        </form><div className="review-box"><h3>{app.manual_submission_required ? "Review before browser filling" : "Review prepared answers"}</h3><p className="small muted">{app.manual_submission_required ? "Check and confirm your answers here. The agent rechecks the employer form without sending your answers. After your approval, it opens a visible browser and fills supported fields. You finish custom controls and submit yourself." : "Check the prepared answers. Turio rechecks the employer form; nothing is submitted until your final approval."}</p><button className="button primary" style={{ marginTop: 16 }} disabled={locked || dirty} onClick={() => act("/review")}>Prepare final review</button>{dirty && <p className="small muted">Save your changes first.</p>}</div>
        {app.review_token && !dirty && app.status === "ready_for_review" && <div className="review-box"><h3>Ready for your decision</h3><p>{app.manual_submission_required ? `Opening the filled form sends your reviewed answers and original resume to ${app.job.company}. The agent never clicks Submit Application. The browser stays open for up to 15 minutes.` : `Review every answer above. Submitting sends this exact reviewed information to ${app.job.company}.`}</p><label className="check-label" style={{ marginTop: 16 }}><input type="checkbox" checked={approved} disabled={reviewExpired} onChange={e => setApproved(e.target.checked)} />{app.manual_submission_required ? "I approve sending these reviewed answers and my original resume to the employer form. I will submit it myself." : "I have reviewed all answers and explicitly approve submitting this application."}</label><button className="button primary" style={{ marginTop: 16 }} disabled={!approved || busy || reviewExpired} onClick={() => { approvalKey.current ||= requestKey(); void act(app.manual_submission_required ? "/handoff" : "/approve-submit", { approved: true, review_token: app.review_token }, "POST", approvalKey.current); }}>{app.manual_submission_required ? "Open filled employer form" : "Approve & submit application"}</button><p className="small muted" style={{ marginTop: 10 }}>{reviewExpired ? "This review has expired (15-minute limit). Click 'Prepare final review' above to generate a fresh review." : reviewRemainingMs !== null ? `Reviews expire after 15 minutes (${Math.ceil(reviewRemainingMs / 60000)} min remaining). Changes require a fresh review.` : "Reviews expire after 15 minutes. Changes require a fresh review."}</p></div>}
      </section>}
      <section className="panel detail-panel" style={{ marginTop: 24 }}><h2>Activity</h2><ol className="timeline">{app.events.map((event, i) => <li key={i}><p>{event.event_type.replaceAll("_", " ")}</p><time>{new Date(event.created_at).toLocaleString()}</time>{typeof event.event_data.message === "string" && <p className="small muted">{event.event_data.message}</p>}</li>)}</ol></section>
    </div><aside className="panel detail-panel detail-aside"><h2>Keep track</h2><p className="small muted">Recruiter outcomes are separate from application preparation.</p><form onSubmit={e => { e.preventDefault(); void act("", { notes: notes || null, outcome: outcome || null }, "PATCH"); }}><label style={{ marginTop: 20 }}>Outcome<Select label="Outcome" value={outcome} onChange={setOutcome} placeholder="Not recorded" options={[{ value: "", label: "Not recorded" }, ...outcomes.map(value => ({ value, label: value.replaceAll("_", " ") }))]} /></label><label style={{ marginTop: 20 }}>Notes<textarea value={notes} maxLength={10000} onChange={e => setNotes(e.target.value)} placeholder="Interview dates, follow-ups, useful details…" /></label><button className="button secondary full" disabled={busy}>Save tracking</button></form>
        {app.submission_method && <Notice>Submission recorded via {app.submission_method}. {app.submitted_at && new Date(app.submitted_at).toLocaleDateString()}</Notice>}
        {!["submitted", "cancelled", "submitting", "preparing"].includes(app.status) && <div style={{ marginTop: 24 }}><label className="check-label small"><input type="checkbox" checked={manual} onChange={e => setManual(e.target.checked)} />I submitted this application myself on the employer site.</label><button className="button secondary full" disabled={!manual || busy} onClick={() => act("", { submitted_manually: true }, "PATCH")}>Record manual submission</button><button className="text-button" style={{ marginTop: 20 }} disabled={busy} onClick={() => act("", { cancel: true }, "PATCH")}>Cancel this application</button></div>}
      </aside></div>
  </>}</Workspace>;
}
