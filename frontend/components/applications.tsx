"use client";
import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, requestKey, safeExternalUrl } from "@/lib/api";
import type { Application, ApplicationPage, Field } from "@/lib/types";
import { useSession } from "./session";
import { CompanyLogo, Empty, Loading, Notice, PageHeading, Pagination, Status, Workspace } from "./ui";

const outcomes = ["under_review", "interview", "offer", "rejected", "withdrawn", "accepted"];
const statuses = ["created", "preparing", "needs_input", "ready_for_review", "submitting", "submitted", "verification_failed", "automation_failed", "cancelled"];
export function Applications({ initialOutcome = "", interviews = false }: { initialOutcome?: string; interviews?: boolean }) {
  const { user } = useSession(); const [data, setData] = useState<ApplicationPage | null>(null);
  const [outcome, setOutcome] = useState(interviews ? "interview" : initialOutcome); const [status, setStatus] = useState("");
  const [offset, setOffset] = useState(0); const [error, setError] = useState(""); const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!user) return;
    let active = true; setLoading(true); setError("");
    api<ApplicationPage>(`/applications?limit=12&offset=${offset}${status ? `&status=${status}` : ""}${outcome ? `&outcome=${outcome}` : ""}`)
      .then(value => { if (active) setData(value); }).catch(error => { if (active) setError(error.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [user, offset, status, outcome]);
  return <Workspace><PageHeading eyebrow="Every step, in one place" title={interviews ? "The conversation starts here." : "Your next chapters."} action={<Link className="button primary" href="/jobs">Find opportunities ↗</Link>}>{interviews ? "Keep interview-stage opportunities and your follow-up notes close." : "Prepare with care. Track your progress. Keep moving forward."}</PageHeading>
    <div className="filters panel"><label>Application status<select value={status} onChange={e => { setStatus(e.target.value); setOffset(0); }}><option value="">All statuses</option>{statuses.map(s => <option key={s} value={s}>{s.replaceAll("_", " ")}</option>)}</select></label>{!interviews && <label>Outcome<select value={outcome} onChange={e => { setOutcome(e.target.value); setOffset(0); }}><option value="">All outcomes</option>{outcomes.map(s => <option key={s} value={s}>{s.replaceAll("_", " ")}</option>)}</select></label>}</div>
    {error && <Notice kind="error">{error}</Notice>}{loading ? <Loading /> : data && (data.applications.length ? <><div className="panel table-wrap"><table className="data-table"><thead><tr><th scope="col">Opportunity</th><th scope="col">Status</th><th scope="col">Outcome</th><th scope="col">Started</th><th scope="col"><span className="small">Review</span></th></tr></thead><tbody>{data.applications.map(app => <tr key={app.id}><td><Link className="table-job" href={`/applications/${app.id}`}><CompanyLogo job={app.job} /><span><strong>{app.job.title}</strong><br /><span className="muted small">{app.job.company}</span></span></Link></td><td><Status value={app.status} /></td><td>{app.outcome?.replaceAll("_", " ") || "Not recorded"}</td><td>{new Date(app.created_at).toLocaleDateString()}</td><td><Link className="inline-link" aria-label={`Review ${app.job.title}`} href={`/applications/${app.id}`}>↗</Link></td></tr>)}</tbody></table></div><Pagination total={data.total} offset={offset} onChange={setOffset} /></> :
      <Empty title={interviews ? "The next conversation is ahead." : "Your first step belongs here."} action={<Link href="/jobs" className="button secondary">Explore jobs</Link>}>{interviews ? "Applications marked with the interview outcome will appear here. Record dates and follow-ups in the application's notes." : "No applications match these filters. Start from a job posting to prepare and track an application."}</Empty>)}
  </Workspace>;
}

export function ApplicationDetail({ applicationId, reviewMode = false }: { applicationId: string; reviewMode?: boolean }) {
  const { user } = useSession();
  const [app, setApp] = useState<Application | null>(null); const [fields, setFields] = useState<Field[]>([]);
  const [reuse, setReuse] = useState<Record<string, boolean>>({}); const [notes, setNotes] = useState(""); const [outcome, setOutcome] = useState("");
  const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [notice, setNotice] = useState("");
  const [approved, setApproved] = useState(false); const [manual, setManual] = useState(false); const [dirty, setDirty] = useState(false);
  const approvalKey = useRef<Record<string, string> | null>(null);
  const prefix = `/applications/${applicationId}`;
  function populate(value: Application) { setApp(value); setFields(value.fields); setNotes(value.notes || ""); setOutcome(value.outcome || ""); setDirty(false); setApproved(false); }
  useEffect(() => { if (user) api<Application>(prefix).then(populate).catch(error => setError(error.message)); }, [user, prefix]);
  async function act(path: string, payload?: object, method = "POST", headers?: Record<string, string>) {
    setBusy(true); setError(""); setNotice("");
    try { populate(await api<Application>(prefix + path, { method, headers, body: payload ? JSON.stringify(payload) : undefined })); setNotice("Application updated."); }
    catch (error) { setError((error as Error).message); } finally { setBusy(false); }
  }
  function change(id: string, value: string | boolean | null) { setFields(items => items.map(f => f.id === id ? { ...f, value, user_confirmed: true } : f)); setDirty(true); setApproved(false); }
  async function saveAnswers(event: FormEvent) {
    event.preventDefault();
    await act("/answers", { answers: fields.filter(f => f.value_source !== "profile").map(f => ({ field_id: f.id, value: f.value, user_confirmed: f.user_confirmed, save_for_reuse: !!reuse[f.id] })) }, "POST", requestKey());
  }
  const locked = busy || !!app && ["preparing", "submitting", "submitted", "cancelled", "verification_failed"].includes(app.status);
  return <Workspace><Link className="inline-link" href="/applications">← All applications</Link>{error && <Notice kind="error">{error}</Notice>}{notice && <Notice kind="success">{notice}</Notice>}{!app ? !error && <Loading /> : <>
    <div style={{ marginTop: 28 }}><PageHeading eyebrow={app.job.company} title={reviewMode ? "One last look." : app.job.title} action={<Status value={app.status} />}>Your information. Your review. Your final decision.</PageHeading></div>
    <div className="two-column"><div><section className="panel detail-panel"><h2>Application preparation</h2><p className="muted">Browser assistance is experimental and may be unavailable for this posting. You can always continue on the employer site and record your progress here.</p>
      <p className="small muted">{app.resume_id ? "Your stored resume and profile will be reused. No per-job upload is needed." : <>No resume selected yet. <Link className="inline-link" href="/profile">Upload a PDF in your profile</Link>, then return here.</>} The agent prepares fields only; you must review and explicitly approve before submission.</p><div className="actions" style={{ marginTop: 20 }}><a className="button secondary" href={safeExternalUrl(app.application_url)} target="_blank" rel="noopener noreferrer">Open employer application ↗</a><button className="button primary" disabled={locked} onClick={() => act("/start")}>{busy ? "Working…" : "Apply with Agent"}</button><button className="text-button" disabled={busy} onClick={() => act("/recover")}>Check status</button></div>
      {app.fields.length > 0 && <><h3>Required-field readiness · {Math.round(app.readiness_score * 100)}%</h3><div className="progress-track"><span style={{ width: `${app.readiness_score * 100}%` }} /></div><p className="small muted">This measures confirmed required fields, not hiring likelihood or live submission success.</p></>}
      {app.status === "verification_failed" && <Notice kind="error">The submission outcome is uncertain. Check the employer site before any manual retry. Automatic resubmission is disabled.</Notice>}
    </section>
    {app.fields.length > 0 && <section className="panel detail-panel" style={{ marginTop: 24 }}><h2>Review your answers</h2><p className="small muted" style={{ marginBottom: 22 }}>Profile values are reused automatically. To change them, edit your profile and prepare again. Every other answer remains yours to confirm.</p><form onSubmit={saveAnswers}>
      {fields.map(field => <div className="field-row" key={field.id}><label>{field.label}{field.required ? " *" : " (optional)"}
        {field.input_type === "file" ? <span className="muted small">{field.value ? "Your stored original resume is selected." : "No resume selected. Upload one in your profile, then use Apply with Agent again."}</span> :
          field.input_type === "checkbox" ? <input type="checkbox" checked={field.value === true} disabled={locked || field.value_source === "profile"} onChange={e => change(field.id, e.target.checked)} /> :
          field.input_type === "select" ? <select value={String(field.value ?? "")} disabled={locked || field.value_source === "profile"} onChange={e => change(field.id, e.target.value || null)}><option value="">Choose an answer</option>{field.options.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select> :
          field.input_type === "textarea" ? <textarea maxLength={10000} value={String(field.value ?? "")} disabled={locked || field.value_source === "profile"} onChange={e => change(field.id, e.target.value || null)} /> :
          <input type={["email", "tel", "url", "number"].includes(field.input_type) ? field.input_type : "text"} maxLength={10000} value={String(field.value ?? "")} disabled={locked || field.value_source === "profile"} onChange={e => change(field.id, e.target.value || null)} />}</label>
        <p className="small muted">{field.value_source === "profile" ? "From your stored profile" : field.value_source === "draft" ? "Factual starter from your profile — review and confirm before using." : field.user_confirmed ? "Confirmed answer" : "Needs your confirmation"}</p>
        {field.input_type === "textarea" && field.normalized_intent === "custom" && <button type="button" className="button secondary small" style={{ marginTop: 12 }} disabled={locked || dirty} onClick={() => act(`/fields/${field.id}/draft`)}>Draft from profile</button>}
        {field.value_source !== "profile" && <><label className="check-label"><input type="checkbox" checked={field.user_confirmed} disabled={locked} onChange={e => { setFields(items => items.map(f => f.id === field.id ? { ...f, user_confirmed: e.target.checked } : f)); setDirty(true); setApproved(false); }} />I confirm this answer is accurate.</label><label className="check-label small muted"><input type="checkbox" checked={!!reuse[field.id]} disabled={locked} onChange={e => { setReuse(values => ({ ...values, [field.id]: e.target.checked })); setDirty(true); }} />Save for this exact question in future applications.</label></>}</div>)}
      {fields.some(f => f.value_source !== "profile") && <button className="button secondary" disabled={locked || !dirty}>Save answers</button>}
    </form><div className="review-box"><h3>Fill, validate, then review</h3><p className="small muted">This step fills supported fields and checks them without submitting. Your final approval comes separately.</p><button className="button primary" style={{ marginTop: 16 }} disabled={locked || dirty} onClick={() => act("/review")}>Prepare final review</button>{dirty && <p className="small muted">Save your changes first.</p>}</div>
    {app.review_token && !dirty && app.status === "ready_for_review" && <div className="review-box"><h3>Ready for your decision</h3><p>Review every answer above. Submitting sends this exact reviewed information to {app.job.company}.</p><label className="check-label" style={{ marginTop: 16 }}><input type="checkbox" checked={approved} onChange={e => setApproved(e.target.checked)} />I have reviewed all answers and explicitly approve submitting this application.</label><button className="button primary" style={{ marginTop: 16 }} disabled={!approved || busy} onClick={() => { approvalKey.current ||= requestKey(); void act("/approve-submit", { approved: true, review_token: app.review_token }, "POST", approvalKey.current); }}>Approve & submit application</button><p className="small muted" style={{ marginTop: 10 }}>Reviews expire after 15 minutes. Changes require a fresh review.</p></div>}
    </section>}
    <section className="panel detail-panel" style={{ marginTop: 24 }}><h2>Activity</h2><ol className="timeline">{app.events.map((event, i) => <li key={i}><p>{event.event_type.replaceAll("_", " ")}</p><time>{new Date(event.created_at).toLocaleString()}</time>{typeof event.event_data.message === "string" && <p className="small muted">{event.event_data.message}</p>}</li>)}</ol></section>
    </div><aside className="panel detail-panel detail-aside"><h2>Keep track</h2><p className="small muted">Recruiter outcomes are separate from application preparation.</p><form onSubmit={e => { e.preventDefault(); void act("", { notes: notes || null, outcome: outcome || null }, "PATCH"); }}><label style={{ marginTop: 20 }}>Outcome<select value={outcome} onChange={e => setOutcome(e.target.value)}><option value="">Not recorded</option>{outcomes.map(value => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</select></label><label style={{ marginTop: 20 }}>Notes<textarea value={notes} maxLength={10000} onChange={e => setNotes(e.target.value)} placeholder="Interview dates, follow-ups, useful details…" /></label><button className="button secondary full" disabled={busy}>Save tracking</button></form>
      {app.submission_method && <Notice>Submission recorded via {app.submission_method}. {app.submitted_at && new Date(app.submitted_at).toLocaleDateString()}</Notice>}
      {!["submitted", "cancelled", "submitting", "preparing"].includes(app.status) && <div style={{ marginTop: 24 }}><label className="check-label small"><input type="checkbox" checked={manual} onChange={e => setManual(e.target.checked)} />I submitted this application myself on the employer site.</label><button className="button secondary full" disabled={!manual || busy} onClick={() => act("", { submitted_manually: true }, "PATCH")}>Record manual submission</button><button className="text-button" style={{ marginTop: 20 }} disabled={busy} onClick={() => act("", { cancel: true }, "PATCH")}>Cancel this application</button></div>}
    </aside></div>
  </>}</Workspace>;
}
