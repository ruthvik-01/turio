"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { MatchPage, Profile, Summary } from "@/lib/types";
import { useSession } from "./session";
import { Empty, JobCard, Loading, Notice, Workspace } from "./ui";

export function Dashboard() {
  const { user } = useSession();
  const [data, setData] = useState<{ profile: Profile; summary: Summary } | null>(null);
  const [matches, setMatches] = useState<MatchPage | null>(null);
  const [matchError, setMatchError] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    if (!user) return;
    let active = true;
    Promise.all([api<Profile>("/profiles/me"), api<Summary>("/applications/summary")])
      .then(([profile, summary]) => { if (active) setData({ profile, summary }); })
      .catch(error => { if (active) setError(error.message); });
    api<MatchPage>("/matches?limit=3").then(value => { if (active) setMatches(value); })
      .catch(error => { if (active) setMatchError(error.message); });
    return () => { active = false; };
  }, [user]);
  const s = data?.summary;
  const needsAttention = s?.needs_attention ?? 0;
  const submitted = s?.total ? s.submitted / s.total * 100 : 0;
  const active = s?.total ? s.in_progress / s.total * 100 : 0;
  const attention = s?.total ? needsAttention / s.total * 100 : 0;
  return <Workspace>{error && <Notice kind="error">{error}</Notice>}{!data && !error ? <Loading /> : data && s && <>
    <section className="dashboard-hero"><div><p className="eyebrow">Good to see you{data.profile.full_name ? `, ${data.profile.full_name.split(" ")[0]}` : ""}</p><h1>Home</h1><p className="hero-copy">Check your application progress or browse jobs.</p>
      <div className="actions"><Link className="button primary" href="/jobs">Browse jobs <span aria-hidden>↗</span></Link><Link className="button secondary" href="/profile">Update profile</Link></div></div></section>
    <section className="stats" aria-label="Your progress">{[
      [s.total, "Applications", "/applications"], [s.interviews, "Interviews", "/interviews"],
      [s.offers, "Offers", "/applications?outcome=offer"], [s.in_progress, "In progress", "/applications"],
    ].map(([count, label, href]) => <Link className="stat-card panel" href={String(href)} key={label}><div><strong>{count}</strong><small>{label}</small></div><span className="chevron" aria-hidden>›</span></Link>)}</section>
    <section className="analytics-row"><article className="panel chart-panel"><div className="chart-heading"><h2>Applications over time</h2><span className="small muted">Last 4 weeks · UTC</span></div>
      <div className="bar-chart" role="group" aria-label={`${s.days.reduce((sum, day) => sum + day.count, 0)} applications created in the last 28 days`}>{s.days.map(day => <div key={day.date} tabIndex={0} role="img" aria-label={`${day.date}: ${day.count} applications`} title={`${day.date}: ${day.count}`}><span className="bar-mark" style={{ height: `${day.count / Math.max(1, ...s.days.map(d => d.count)) * 100}%` }} /><span className="chart-tooltip" aria-hidden>{day.count} · {day.date}</span></div>)}</div>
      <div className="chart-axis"><span>{s.days[0]?.date.slice(5)}</span><span>{s.days[13]?.date.slice(5)}</span><span>{s.days[27]?.date.slice(5)}</span></div>
      {!s.total && <p className="small muted" style={{ marginTop: 12 }}>Application counts appear here once you create an application.</p>}<details><summary>View daily counts</summary><table><caption className="small muted">Applications created · Last 28 days · UTC</caption><thead><tr><th scope="col">Date</th><th scope="col">Applications</th></tr></thead><tbody>{s.days.map(day => <tr key={day.date}><th scope="row">{day.date}</th><td>{day.count}</td></tr>)}</tbody></table></details></article>
      <article className="panel chart-panel"><div className="chart-heading"><h2>Application status</h2><span className="small muted">All time</span></div><div className="donut-layout"><div className="donut" role="img" aria-label={needsAttention ? `${s.submitted} submitted, ${s.in_progress} in progress, ${needsAttention} need attention, ${s.cancelled} cancelled` : `${s.submitted} submitted, ${s.in_progress} in progress, ${s.cancelled} cancelled`} style={{ background: s.total ? `conic-gradient(var(--chart-submitted) 0 ${submitted}%,var(--chart-active) ${submitted}% ${submitted + active}%,var(--error) ${submitted + active}% ${submitted + active + attention}%,var(--chart-cancelled) ${submitted + active + attention}% 100%)` : "var(--neutral-soft)" }}><div className="donut-center">{s.total}<small>applications</small></div></div><div className="legend"><span><i style={{ background: "var(--chart-submitted)" }} />Submitted {s.submitted}</span><span><i style={{ background: "var(--chart-active)" }} />In progress {s.in_progress}</span><span><i style={{ background: "var(--chart-cancelled)" }} />Cancelled {s.cancelled}</span></div></div>{needsAttention > 0 && <p className="small muted" style={{ marginTop: 12 }}>Needs attention: {needsAttention}</p>}<details><summary>View status counts</summary><table><caption className="small muted">Application status · All time</caption><thead><tr><th scope="col">Status</th><th scope="col">Applications</th></tr></thead><tbody><tr><th scope="row">Submitted</th><td>{s.submitted}</td></tr><tr><th scope="row">In progress</th><td>{s.in_progress}</td></tr><tr><th scope="row">Needs attention</th><td>{needsAttention}</td></tr><tr><th scope="row">Cancelled</th><td>{s.cancelled}</td></tr></tbody></table></details></article></section>
    <div className="section-title"><h2>Recommended for you</h2><Link className="inline-link" href="/jobs">Explore opportunities ↗</Link></div>
    {matchError ? <Notice kind="error">{matchError} <Link className="inline-link" href="/jobs">Open recommendations</Link></Notice> : !matches ? <p role="status" className="small muted">Loading recommendations…</p> : matches.matches.length ? <div className="job-grid">{matches.matches.map(match => <JobCard key={match.id} job={match.job} match={match} />)}</div> :
      <Empty title={matches.stale ? "Recommendations need updating" : "No recommendations yet"} action={<Link className="button secondary" href="/jobs">Find recommendations</Link>}>{matches.stale ? "Refresh your matches to use your latest profile and the current job inventory." : "Add your skills and experience, then generate recommendations from the jobs in your inventory."}</Empty>}
    <section style={{ marginTop: 24 }}><article className="focus-card panel"><h2>Quick links</h2><Link className="focus-item" href="/profile"><span>{data.profile.skills.length ? "Keep your profile up to date" : "Add your skills to your profile"}</span><span>↗</span></Link><Link className="focus-item" href="/jobs"><span>Browse the job inventory</span><span>↗</span></Link><Link className="focus-item" href="/applications"><span>Review your applications</span><span>↗</span></Link></article></section>
  </>}</Workspace>;
}
