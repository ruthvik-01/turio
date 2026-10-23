"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, ApiError, requestKey, runTask, safeExternalUrl } from "@/lib/api";
import type { Application, Job, JobPage, Match, MatchPage, Method } from "@/lib/types";
import { useSession } from "./session";
import { CompanyFilter } from "./company-filter";
import { Select } from "./select";
import { Badge, Empty, JobCard, Loading, Notice, PageHeading, Pagination, Workspace } from "./ui";

import { BulkApplications } from "./bulk-applications";

export function Jobs() {
  const { user } = useSession();
  const [tab, setTab] = useState<"all" | "matches">("all");
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [method, setMethod] = useState<Method>("sbert");
  const [platform, setPlatform] = useState("");
  const [jobs, setJobs] = useState<JobPage | null>(null);
  const [matches, setMatches] = useState<MatchPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [version, setVersion] = useState(0);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [selected, setSelected] = useState<Record<string, Job>>({});
  function removeUnavailableJob(id: string) {
    setSelected(items=>{ const next={...items}; delete next[id]; return next; });
    setJobs(page=>page ? {...page,jobs:page.jobs.filter(item=>item.id!==id),total:Math.max(0,page.total-1)} : page);
    setMatches(page=>page ? {...page,matches:page.matches.filter(item=>item.job.id!==id),total:Math.max(0,page.total-1)} : page);
    setVersion(value=>value+1);
  }
  useEffect(() => {
    if (!user) return;
    let active = true;
    setLoading(true); setError("");
    const task = tab === "all"
      ? api<JobPage>(`/jobs?limit=12&offset=${offset}&${query}`).then(value => { if (active) setJobs(value); })
      : api<MatchPage>(`/matches?method=${method}&limit=12&offset=${offset}`).then(value => { if (active) setMatches(value); });
    task.catch(error => { if (active) setError(error.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [user, tab, query, offset, method, version]);
  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = new FormData(event.currentTarget); const params = new URLSearchParams();
    data.forEach((value, key) => { if (String(value).trim()) params.set(key, String(value).trim()); });
    setQuery(params.toString()); setOffset(0);
  }
  async function generate() {
    setBusy(true); setError(""); setNotice("Generating recommendations. Large inventories can take a few minutes.");
    try { await runTask("matches_refresh", method, run => setNotice(run.state === "queued" ? "Recommendations queued. Waiting for the worker…" : "Generating recommendations in the background…")); setOffset(0); setVersion(v => v + 1); setNotice("Recommendations updated using your current profile."); }
    catch (error) { setError((error as Error).message); setNotice(""); } finally { setBusy(false); }
  }
  async function refreshJobs() {
    setBusy(true); setError(""); setNotice("Refreshing the configured dataset. Keep this page open.");
    try {
      const result = await runTask<{ inserted: number; updated: number; unchanged: number }>("jobs_refresh", undefined,
        run => setNotice(run.state === "queued" ? "Inventory refresh queued. Waiting for the worker…" : "Refreshing the inventory in the background…"));
      setNotice(`Inventory refreshed: ${result.inserted} new, ${result.updated} changed, ${result.unchanged} unchanged.`);
      setVersion(v => v + 1); setOffset(0);
    } catch (error) { setError((error as Error).message); setNotice(""); } finally { setBusy(false); }
  }
  function jobSelection(job: Job) {
    return <label className="check-label small"><input type="checkbox" aria-label={`Select ${job.title} at ${job.company}`} checked={!!selected[job.id]} disabled={busy} onChange={e => { setSelected(values => { const next = { ...values }; if (e.target.checked) next[job.id] = job; else delete next[job.id]; return next; }); }} />Select for bulk application</label>;
  }
  const visibleJobs = tab === "all" ? jobs?.jobs ?? [] : matches?.matches.map(match => match.job) ?? [];
  return <Workspace><PageHeading eyebrow="" title="Jobs" action={<button className="button secondary small" disabled={busy} onClick={refreshJobs}>Refresh inventory</button>}>Search by title, company or location, or compare jobs with your profile.</PageHeading>
    <div className="tabs" role="tablist" aria-label="Job views">{[["all", "All opportunities"], ["matches", "For you"]].map(([key, title]) => <button role="tab" aria-selected={tab === key} className={tab === key ? "active" : ""} key={key} onClick={() => { setTab(key as typeof tab); setOffset(0); }}>{title}</button>)}</div>
    {tab === "all" ? <form className="filters panel" onSubmit={search}><label className="search-filter">Search<input name="q" placeholder="Job title or company…" /></label><CompanyFilter /><label>Location<input name="location" placeholder="City or country" /></label><label>Platform (Ashby supported)<Select label="Platform (Ashby supported)" name="ats" value={platform} onChange={setPlatform} options={[{ value: "", label: "All platforms" }, { value: "ashby", label: "Ashby" }]} /></label><button className="button primary" type="submit">Search</button></form> :
      <div className="filters panel"><label>Matching method<Select label="Matching method" value={method} onChange={value => { setMethod(value as Method); setOffset(0); }} options={[{ value: "sbert", label: "SBERT semantic + structured signals" }]} /></label><button className="button primary" disabled={busy} onClick={generate}>{busy ? "Working…" : "Refresh my matches"}</button></div>}
    {error && <Notice kind="error">{error}</Notice>}{notice && <Notice>{notice}</Notice>}
    <BulkApplications selected={selected} onSelect={setSelected} visibleJobs={visibleJobs} loading={loading}
      externalBusy={busy} onBusyChange={setBusy} onUnavailable={removeUnavailableJob} />
    {loading ? <Loading /> : tab === "all" ? jobs && (jobs.jobs.length ? <><div className="job-grid">{jobs.jobs.map(job => <JobCard key={job.id} job={job} selection={jobSelection(job)} />)}</div><Pagination offset={offset} total={jobs.total} onChange={setOffset} /></> :
      <Empty title="No jobs found">No jobs match these filters, or your job inventory has not been imported yet. Try a broader search or refresh the configured dataset.</Empty>) :
      matches && (matches.matches.length ? <><p className="small muted" style={{ marginBottom: 20 }}>Scores describe relevance, not hiring probability. Open an opportunity to see the evidence.</p><div className="job-grid">{matches.matches.map(match => <JobCard key={match.id} job={match.job} match={match} selection={jobSelection(match.job)} />)}</div><Pagination offset={offset} total={matches.total} onChange={setOffset} /></> :
        <Empty title={matches.stale ? "Recommendations need updating" : "No recommendations yet"} action={<Link className="button secondary" href="/profile">Review profile</Link>}>{matches.stale ? "Your profile, inventory or ranking configuration changed. Refresh your matches." : "Add your skills and experience, then refresh your matches using the method above."}</Empty>)}
  </Workspace>;
}

export function JobDetail({ jobId, matchId }: { jobId: string; matchId?: string }) {
  const { user } = useSession(); const router = useRouter();
  const [job, setJob] = useState<Job | null>(null); const [match, setMatch] = useState<Match | null>(null);
  const [error, setError] = useState(""); const [staleNotice, setStaleNotice] = useState(""); const [busy, setBusy] = useState(false);
  const key = useRef<Record<string, string> | null>(null);
  useEffect(() => {
    if (!user) return;
    api<Job>(`/jobs/${jobId}`).then(setJob).catch(error => setError(error.message));
    if (matchId) api<Match>(`/matches/${matchId}`).then(value => { setMatch(value); setStaleNotice(""); }).catch(error => { if (error instanceof ApiError && error.status === 409) setStaleNotice(error.message || "This recommendation comes from an older match snapshot. Refresh your matches to see updated relevance details."); else setError((error as Error).message); });
  }, [user, jobId, matchId]);
  async function refreshFromDetail() { setBusy(true); setError(""); try { await runTask("matches_refresh", "sbert"); const value = await api<MatchPage>("/matches?limit=50&offset=0"); const updated = value.matches.find(item => item.job.id === jobId); setMatch(updated ?? null); setStaleNotice(""); if (!updated) router.push("/jobs?tab=matches"); } catch (error) { setError((error as Error).message); } finally { setBusy(false); } }
  async function apply() {
    setBusy(true); setError(""); key.current ||= requestKey();
    try { const app = await api<Application>("/applications", { method: "POST", headers: key.current, body: JSON.stringify({ job_id: jobId, reuse_existing: true }) }); router.push(`/applications/${app.id}`); }
    catch (error) { setError((error as Error).message); } finally { setBusy(false); }
  }
  return <Workspace><Link className="inline-link" href="/jobs">← All opportunities</Link>{error && <Notice kind="error">{error}</Notice>}{staleNotice && <Notice>{staleNotice} <button type="button" className="text-button" style={{ marginLeft: 8 }} disabled={busy} onClick={refreshFromDetail}>Refresh recommendations</button></Notice>}{!job ? <Loading /> : <>
    <div style={{ marginTop: 28 }}><PageHeading eyebrow={job.company} title={job.title}>{job.location || "Location not specified"}</PageHeading></div>
    <div className="two-column"><article className="panel detail-panel"><h2>About this opportunity</h2><div className="prose">{job.description || "No description was supplied by the job source. Check the original posting."}</div><h3>Extracted skills</h3><div className="chips">{job.required_skills.map(skill => <Badge key={skill}>{skill}</Badge>)}</div>
      {match && <><h3>Why this appeared for you</h3><p>{match.explanation.summary}</p><dl>{Object.entries(match.explanation.scores).map(([name, score]) => <div className="focus-item" key={name}><dt>{name}</dt><dd>{score === null ? "Not enough evidence" : `${Math.round(score * 100)}/100`}</dd></div>)}</dl><p className="small muted">{match.explanation.disclaimer}</p></>}</article>
      <aside className="panel detail-panel detail-aside"><h2>Apply for this job</h2><p className="muted">Create an application to prepare your answers and track its status.</p><dl><dt>Company</dt><dd>{job.company}</dd><dt>Location</dt><dd>{job.location || "Not specified"}</dd><dt>Source</dt><dd>{job.ats || "Job dataset"}</dd>{match && <><dt>Relevance · {match.method}</dt><dd>{Math.round(match.final_score * 100)}/100</dd></>}</dl>
      <button className="button primary full" disabled={busy} onClick={apply}>{busy ? "Creating…" : "Prepare application ↗"}</button><a className="button secondary full" href={safeExternalUrl(job.application_url || job.job_url)} target="_blank" rel="noopener noreferrer">Original posting ↗</a><p className="small muted" style={{ marginTop: 16 }}>Creating an application does not submit anything.</p></aside></div>
  </>}</Workspace>;
}
