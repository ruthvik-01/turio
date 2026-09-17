"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { api } from "@/lib/api";
import type { Job, Match } from "@/lib/types";
import { useSession } from "./session";

export function Header() {
  const path = usePathname();
  const router = useRouter();
  const { user, clearForLogout } = useSession();
  const [error, setError] = useState("");
  async function logout() {
    try { await api("/auth/logout", { method: "POST", body: "{}" }); clearForLogout(); router.push("/"); }
    catch (error) { setError((error as Error).message); }
  }
  return <><header className="site-header">
    <Link href={user ? "/home" : "/"} className="brand" aria-label="Turio home"><img src="/brand/turio-logo.png" alt="Turio" /></Link>
    {user && <nav aria-label="Main navigation">{[["/home", "Home"], ["/jobs", "Jobs"], ["/applications", "Applications"], ["/interviews", "Interviews"], ["/resources", "Resources"]].map(([href, text]) =>
      <Link key={href} href={href} aria-current={path.startsWith(href) ? "page" : undefined}>{text}</Link>)}</nav>}
    <div className="header-actions">{user ? <><Link className="avatar" href="/profile" aria-label="Edit profile">{user.email[0].toUpperCase()}</Link><button className="text-button" onClick={logout}>Sign out</button></> :
      <><Link className="text-button" href="/login">Sign in</Link><Link className="button primary small" href="/signup">Get started <span aria-hidden>↗</span></Link></>}</div>
  </header>{error && <div className="container"><Notice kind="error">{error}</Notice></div>}</>;
}
export function Workspace({ children }: { children: ReactNode }) {
  const { user, loading, loggingOut } = useSession();
  const router = useRouter();
  useEffect(() => { if (!loading && !user && !loggingOut) router.replace("/login"); }, [loading, user, loggingOut, router]);
  if (loading || !user) return <main className="container"><Loading /></main>;
  return <main className="container workspace">{children}</main>;
}
export function Notice({ children, kind = "info" }: { children: ReactNode; kind?: "error" | "info" | "success" }) { return <div className={`notice ${kind}`} role={kind === "error" ? "alert" : "status"}>{children}</div>; }
export function Loading() { return <div className="loading" role="status"><span className="spinner" /> Loading your workspace…</div>; }
export function Empty({ title, children, action }: { title: string; children: ReactNode; action?: ReactNode }) {
  return <section className="empty panel"><span className="empty-mark" aria-hidden>↗</span><h2>{title}</h2><p>{children}</p>{action}</section>;
}
export function PageHeading({ eyebrow, title, children, action }: { eyebrow: string; title: string; children?: ReactNode; action?: ReactNode }) {
  return <div className="page-heading"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{children && <p className="muted">{children}</p>}</div>{action}</div>;
}
export function Badge({ children }: { children: ReactNode }) { return <span className="badge">{children}</span>; }
export function Status({ value }: { value: string }) { return <span className={`status status-${value}`}>{value.replaceAll("_", " ")}</span>; }
export function CompanyLogo({ job }: { job: Job }) {
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  const url = job.company_logo_url;
  return <span className="company-icon">{url?.startsWith("https://") && failedUrl !== url
    ? <img src={url} alt={`${job.company} logo`} referrerPolicy="no-referrer" style={{ width: "100%", height: "100%", objectFit: "contain", borderRadius: "inherit" }} onError={() => setFailedUrl(url)} />
    : <svg aria-label="Company logo unavailable" role="img" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M5 21V3h14v18M3 21h18M9 21v-4h6v4M8 7h2m4 0h2M8 11h2m4 0h2" /></svg>}</span>;
}
export function JobCard({ job, match }: { job: Job; match?: Match }) {
  return <article className="job-card panel"><div className="job-card-top"><CompanyLogo job={job} /><div><p className="company-name">{job.company}</p><span className="muted small">{job.location || "Location not specified"}</span></div>{match && <span className="match-score">{Math.round(match.final_score * 100)}<small>/100</small></span>}</div>
    <h3><Link href={`/jobs/${job.id}${match ? `?match=${match.id}` : ""}`}>{job.title}</Link></h3>
    <div className="chips">{job.required_skills.slice(0, 4).map(skill => <Badge key={skill}>{skill}</Badge>)}</div>
    {match && <p className="small muted">{match.method === "sbert" ? "SBERT + structured signals" : `${match.method === "tfidf" ? "TF-IDF" : "Keyword"} baseline + structured signals`}</p>}
    <div className="job-card-footer"><span className="small muted">{job.ats || "Job posting"}</span><Link className="inline-link" href={`/jobs/${job.id}${match ? `?match=${match.id}` : ""}`}>View opportunity <span aria-hidden>↗</span></Link></div></article>;
}
export function Pagination({ offset, total, size = 12, onChange }: { offset: number; total: number; size?: number; onChange: (offset: number) => void }) {
  return <div className="pagination"><span className="muted small">{total ? `${offset + 1}–${Math.min(offset + size, total)} of ${total.toLocaleString()}` : "0 results"}</span><div><button className="button secondary small" disabled={offset === 0} onClick={() => onChange(Math.max(0, offset - size))}>Previous</button><button className="button secondary small" disabled={offset + size >= total} onClick={() => onChange(offset + size)}>Next</button></div></div>;
}
