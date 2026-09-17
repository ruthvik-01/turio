"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { MatchPage, Profile, Summary } from "@/lib/types";
import { GrowthArt } from "./growth-art";
import { useSession } from "./session";
import { Empty, JobCard, Loading, Notice, Workspace } from "./ui";

export function Dashboard() {
  const { user } = useSession();
  const [data, setData] = useState<{ profile: Profile; summary: Summary; matches: MatchPage } | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!user) return;
    let active = true;
    Promise.all([api<Profile>("/profiles/me"), api<Summary>("/applications/summary"), api<MatchPage>("/matches?limit=3")])
      .then(([profile, summary, matches]) => { if (active) setData({ profile, summary, matches }); })
      .catch(error => { if (active) setError(error.message); });
    return () => { active = false; };
  }, [user]);
  const s = data?.summary;
  const submitted = s?.total ? s.submitted / s.total * 100 : 0;
  const active = s?.total ? s.in_progress / s.total * 100 : 0;
  return <Workspace>{error && <Notice kind="error">{error}</Notice>}{!data && !error ? <Loading /> : data && s && <>
    <section className="dashboard-hero"><div><p className="eyebrow">Good to see you{data.profile.full_name ? `, ${data.profile.full_name.split(" ")[0]}` : ""}</p><h1>Keep going.<br /><em>You’re making progress.</em></h1><p className="hero-copy">Find the right opportunities, stay organized, and get closer to the career you want.</p>
      <div className="actions"><Link className="button primary" href="/jobs">Browse jobs <span aria-hidden>↗</span></Link><Link className="button secondary" href="/profile">Update profile</Link></div></div><GrowthArt /></section>
    <section className="stats" aria-label="Your progress">{[
      ["▤", s.total, "Applications", "/applications"], ["♧", s.interviews, "Interviews", "/interviews"],
      ["◇", s.offers, "Offers", "/applications?outcome=offer"], ["◷", s.in_progress, "In progress", "/applications"],
    ].map(([symbol, count, label, href]) => <Link className="stat-card panel" href={String(href)} key={label}><span className="stat-symbol" aria-hidden>{symbol}</span><div><strong>{count}</strong><small>{label}</small></div><span className="chevron" aria-hidden>›</span></Link>)}</section>
    <section className="analytics-row"><article className="panel chart-panel"><div className="chart-heading"><h2>Applications over time</h2><span className="small muted">Last 4 weeks · UTC</span></div>
      <div className="bar-chart" role="img" aria-label={`${s.days.reduce((sum, day) => sum + day.count, 0)} applications created in the last 28 days`}>{s.days.map(day => <div key={day.date} title={`${day.date}: ${day.count}`} style={{ height: `${day.count / Math.max(1, ...s.days.map(d => d.count)) * 100}%` }} />)}</div>
      <div className="chart-axis"><span>{s.days[0]?.date.slice(5)}</span><span>{s.days[13]?.date.slice(5)}</span><span>{s.days[27]?.date.slice(5)}</span></div>
      {!s.total && <p className="small muted" style={{ marginTop: 12 }}>Your timeline will grow with your first application.</p>}</article>
      <article className="panel chart-panel"><div className="chart-heading"><h2>Application status</h2><span className="small muted">All time</span></div><div className="donut-layout"><div className="donut" role="img" aria-label={`${s.submitted} submitted, ${s.in_progress} in progress, ${s.cancelled} cancelled`} style={{ background: `conic-gradient(#9eb783 0 ${submitted}%,#dae4c8 ${submitted}% ${submitted + active}%,#eceee5 ${submitted + active}% 100%)` }}><div className="donut-center">{s.total}<small>applications</small></div></div><div className="legend"><span><i style={{ background: "#9eb783" }} />Submitted {s.submitted}</span><span><i style={{ background: "#dae4c8" }} />In progress {s.in_progress}</span><span><i style={{ background: "#eceee5" }} />Cancelled {s.cancelled}</span></div></div></article></section>
    <div className="section-title"><h2>Recommended for you</h2><Link className="inline-link" href="/jobs">Explore opportunities ↗</Link></div>
    {data.matches.matches.length ? <div className="job-grid">{data.matches.matches.map(match => <JobCard key={match.id} job={match.job} match={match} />)}</div> :
      <Empty title={data.matches.stale ? "Your story has changed." : "Your next fit starts here."} action={<Link className="button secondary" href="/jobs">Find recommendations</Link>}>{data.matches.stale ? "Refresh your matches to use your latest profile and the current job inventory." : "Add your skills and experience, then generate recommendations from the jobs in your inventory."}</Empty>}
    <section className="two-column" style={{ marginTop: 24 }}><article className="focus-card panel"><h2>Today’s focus</h2><Link className="focus-item" href="/profile"><span>{data.profile.skills.length ? "Keep your profile up to date" : "Add your skills to your profile"}</span><span>↗</span></Link><Link className="focus-item" href="/jobs"><span>Find an opportunity worth exploring</span><span>↗</span></Link><Link className="focus-item" href="/applications"><span>Review your next application step</span><span>↗</span></Link></article><aside className="quote-card panel"><p>“A small step is still a step forward.”</p><small>A reminder from Turio</small></aside></section>
  </>}</Workspace>;
}
