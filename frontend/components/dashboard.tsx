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
  const greetingName = data?.profile.full_name?.split(" ")[0] || user?.email.split("@")[0] || "There";
  const inProgress = s?.in_progress ?? 0;
  const total = s?.total ?? 0;

  return <Workspace>{error && <Notice kind="error">{error}</Notice>}{!data && !error ? <Loading /> : data && s && <>
    <section className="dashboard-hero minimal-hero">
      <div>
        <h1>{greetingName}, {inProgress > 0 ? `${inProgress} applications in progress` : total > 0 ? `${total} applications tracked` : "ready to find your next role"}</h1>
        <p className="hero-copy">Check your next steps or explore new roles matching your profile.</p>
        <div className="actions">
          <Link className="button primary" href="/jobs">Browse jobs <span aria-hidden>↗</span></Link>
          <Link className="link" href="/profile">Edit profile</Link>
        </div>
      </div>
    </section>

    {/* Next up: actionable hairline rows (MATTER.MD §7) */}
    <section className="panel next-up-card" aria-label="Next up">
      <div className="section-header-row">
        <h2>Next up</h2>
        <span className="small muted">{s.total} applied · {s.interviews} interviews · {s.offers} offers</span>
      </div>
      <ul className="minimal-list">
        {needsAttention > 0 && (
          <li className="row">
            <span className="row-title">Applications needing review</span>
            <Link className="row-meta" href="/applications"><strong>{needsAttention}</strong> pending ↗</Link>
          </li>
        )}
        <li className="row">
          <span className="row-title">Active applications</span>
          <Link className="row-meta" href="/applications"><strong>{s.in_progress}</strong> in progress ↗</Link>
        </li>
        <li className="row">
          <span className="row-title">New recommended matches</span>
          <Link className="row-meta" href="/jobs"><strong>{matches?.total ?? 0}</strong> roles ↗</Link>
        </li>
      </ul>
    </section>

    {/* Progressive disclosure for analytics (MATTER.MD §4.5 & §7) */}
    <details className="more-panel panel">
      <summary className="more-summary">
        <span>Application insights & daily trends</span>
        <span className="small muted">View charts</span>
      </summary>
      <div className="analytics-row" style={{ marginTop: 16 }}>
        <article className="panel chart-panel">
          <div className="chart-heading"><h2>Applications over time</h2><span className="small muted">Last 4 weeks · UTC</span></div>
          <div className="bar-chart" role="group" aria-label={`${s.days.reduce((sum, day) => sum + day.count, 0)} applications created in the last 28 days`}>{s.days.map(day => <div key={day.date} tabIndex={0} role="img" aria-label={`${day.date}: ${day.count} applications`} title={`${day.date}: ${day.count}`}><span className="bar-mark" style={{ height: `${day.count / Math.max(1, ...s.days.map(d => d.count)) * 100}%` }} /><span className="chart-tooltip" aria-hidden>{day.count} · {day.date}</span></div>)}</div>
          <div className="chart-axis"><span>{s.days[0]?.date.slice(5)}</span><span>{s.days[13]?.date.slice(5)}</span><span>{s.days[27]?.date.slice(5)}</span></div>
          {!s.total && <p className="small muted" style={{ marginTop: 12 }}>Application counts appear here once you create an application.</p>}
          <details><summary>View daily counts</summary><table><caption className="small muted">Applications created · Last 28 days · UTC</caption><thead><tr><th scope="col">Date</th><th scope="col">Applications</th></tr></thead><tbody>{s.days.map(day => <tr key={day.date}><th scope="row">{day.date}</th><td>{day.count}</td></tr>)}</tbody></table></details>
        </article>
        <article className="panel chart-panel">
          <div className="chart-heading"><h2>Application status</h2><span className="small muted">All time</span></div>
          <div className="donut-layout">
            <div className="donut" role="img" aria-label={needsAttention ? `${s.submitted} submitted, ${s.in_progress} in progress, ${needsAttention} need attention, ${s.cancelled} cancelled` : `${s.submitted} submitted, ${s.in_progress} in progress, ${s.cancelled} cancelled`} style={{ background: s.total ? `conic-gradient(var(--chart-submitted) 0 ${submitted}%,var(--chart-active) ${submitted}% ${submitted + active}%,var(--error) ${submitted + active}% ${submitted + active + attention}%,var(--chart-cancelled) ${submitted + active + attention}% 100%)` : "var(--neutral-soft)" }}><div className="donut-center">{s.total}<small>applications</small></div></div>
            <div className="legend"><span><i style={{ background: "var(--chart-submitted)" }} />Submitted {s.submitted}</span><span><i style={{ background: "var(--chart-active)" }} />In progress {s.in_progress}</span><span><i style={{ background: "var(--chart-cancelled)" }} />Cancelled {s.cancelled}</span></div>
          </div>
          {needsAttention > 0 && <p className="small muted" style={{ marginTop: 12 }}>Needs attention: {needsAttention}</p>}
          <details><summary>View status counts</summary><table><caption className="small muted">Application status · All time</caption><thead><tr><th scope="col">Status</th><th scope="col">Applications</th></tr></thead><tbody><tr><th scope="row">Submitted</th><td>{s.submitted}</td></tr><tr><th scope="row">In progress</th><td>{s.in_progress}</td></tr><tr><th scope="row">Needs attention</th><td>{needsAttention}</td></tr><tr><th scope="row">Cancelled</th><td>{s.cancelled}</td></tr></tbody></table></details>
        </article>
      </div>
    </details>

    <div className="section-title"><h2>Recommended for you</h2><Link className="inline-link" href="/jobs">Explore opportunities ↗</Link></div>
    {matchError ? <Notice kind="error">{matchError} <Link className="inline-link" href="/jobs">Open recommendations</Link></Notice> : !matches ? <p role="status" className="small muted">Loading recommendations…</p> : matches.matches.length ? <div className="job-grid">{matches.matches.map(match => <JobCard key={match.id} job={match.job} match={match} />)}</div> :
      <Empty title={matches.stale ? "Recommendations need updating" : "No recommendations yet"} action={<Link className="button secondary" href="/jobs">Find recommendations</Link>}>{matches.stale ? "Refresh your matches to use your latest profile and the current job inventory." : "Add your skills and experience, then generate recommendations from the jobs in your inventory."}</Empty>}
  </>}</Workspace>;
}
