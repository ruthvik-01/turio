"use client";
import { ButtonLabel, TransitionLink as Link } from "./route-motion";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { api } from "@/lib/api";
import type { Job, Match } from "@/lib/types";
import { useSession } from "./session";
import { applyTheme, resolveTheme, type Theme } from "@/lib/theme";

function ThemeToggle() {
  const [theme, setTheme] = useState<Theme | null>(null);
  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const sync = () => setTheme(resolveTheme(document.documentElement.dataset.theme, media.matches));
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);
  return <button id="turio-theme-toggle" type="button" className="text-button theme-toggle"
    aria-label="Dark theme" aria-pressed={theme === null ? undefined : theme === "dark"}
    disabled={theme === null} onClick={() => {
      const next = theme === "dark" ? "light" : "dark";
      applyTheme(next); setTheme(next);
    }}><span className="theme-indicator" aria-hidden="true" /></button>;
}

const NAV_ITEMS: Array<[string, string, ReactNode]> = [
  ["/home", "Home", <svg key="home" aria-hidden="true" className="nav-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5.5v-6h-5v6H4a1 1 0 0 1-1-1v-9.5Z" /></svg>],
  ["/jobs", "Jobs", <svg key="jobs" aria-hidden="true" className="nav-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="7" width="18" height="13" rx="2.5" /><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /></svg>],
  ["/applications", "Applications", <svg key="applications" aria-hidden="true" className="nav-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2" /><rect x="9" y="3" width="6" height="4" rx="1.5" /><path d="m9 14 2 2 4-4" /></svg>],
  ["/interviews", "Interviews", <svg key="interviews" aria-hidden="true" className="nav-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="17" rx="2.5" /><path d="M8 2v4M16 2v4M3 10h18" /></svg>],
  ["/resources", "Resources", <svg key="resources" aria-hidden="true" className="nav-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" /></svg>],
  ["/profile", "Profile", <svg key="profile" aria-hidden="true" className="nav-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="4" /><path d="M5 20a7 7 0 0 1 14 0" /></svg>],
];

export function Header() {
  const path = usePathname();
  const router = useRouter();
  const { user, clearForLogout } = useSession();
  const [error, setError] = useState("");
  const [navOpen, setNavOpen] = useState(false);
  useEffect(() => { setNavOpen(false); }, [path]);
  useEffect(() => {
    if (!navOpen) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setNavOpen(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [navOpen]);
  async function logout() {
    try { await api("/auth/logout", { method: "POST", body: "{}" }); clearForLogout(); router.push("/"); }
    catch (error) { setError((error as Error).message); }
  }
  const publicPage = path === "/" || path === "/login" || path === "/signup";
  const activeItem = NAV_ITEMS.find(([href]) => path.startsWith(href)) ?? NAV_ITEMS[0];
  return <><header className={`site-header${publicPage ? " public-header" : ""}`}>
    {publicPage && <ThemeToggle />}
    <Link href={user ? "/home" : "/"} className="brand" aria-label="Turio home">Turio</Link>
    {user && !publicPage && <nav aria-label="Main navigation" className={navOpen ? "is-open" : undefined}>
      {navOpen && <div className="mobile-nav-backdrop" onClick={() => setNavOpen(false)} aria-hidden="true" />}
      <button
        type="button"
        className="mobile-nav-trigger"
        aria-expanded={navOpen}
        aria-controls="turio-nav-links"
        aria-label="Open navigation menu"
        onClick={() => setNavOpen(open => !open)}
      >
        {activeItem[2]}
        <span>{activeItem[1]}</span>
        <svg className="mobile-nav-chevron" aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m18 15-6-6-6 6" /></svg>
      </button>
      <div id="turio-nav-links" className="nav-links">
        {NAV_ITEMS.map(([href, text, icon]) =>
          <Link key={href} href={href} aria-current={path.startsWith(href) ? "page" : undefined} onClick={() => setNavOpen(false)}>{icon}<span>{text}</span></Link>)}
      </div>
    </nav>}
    <div className="header-actions">
      {!publicPage && <ThemeToggle />}
      {user ? (
        <>
          <Link className="avatar" href="/profile" aria-label="Edit profile">{user.email[0].toUpperCase()}</Link>
          <button className="text-button" onClick={logout}>Sign out</button>
        </>
      ) : (
        <Link className="text-button" href="/login">Sign in</Link>
      )}
    </div>
  </header>{error && <div className="container"><Notice kind="error">{error}</Notice></div>}</>;
}
export function LandingActions() {
  const { user } = useSession();
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);
  return <>
    <div className="actions">
      <Link className="button primary" href={user ? "/home" : "/signup"}>{user ? "Open workspace" : "Get started"}</Link>
      <button type="button" className="button secondary" onClick={() => setOpen(true)}><ButtonLabel>How it works</ButtonLabel></button>
    </div>
    {open && <div className="modal-backdrop" onClick={() => setOpen(false)} role="presentation">
      <div className="modal-card panel" onClick={e => e.stopPropagation()} role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <div className="modal-header">
          <h2 id="modal-title">How Turio works</h2>
          <button type="button" className="modal-close" onClick={() => setOpen(false)} aria-label="Close dialog">✕</button>
        </div>
        <div className="three-column modal-steps">
          <article className="step-card">
            <span>01</span>
            <h3>Add your resume</h3>
            <p>Upload a PDF, check the extracted details and save your profile for future applications.</p>
          </article>
          <article className="step-card">
            <span>02</span>
            <h3>Search jobs</h3>
            <p>Browse the job inventory or compare recommendations with the skills and experience in your profile using SBERT.</p>
          </article>
          <article className="step-card">
            <span>03</span>
            <h3>Prepare an application</h3>
            <p>Reuse your saved answers, review the form and track its status. Submission requires your explicit approval.</p>
          </article>
        </div>
      </div>
    </div>}
  </>;
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
export function JobCard({ job, match, selection }: { job: Job; match?: Match; selection?: ReactNode }) {
  return <article className="job-card panel"><div className="job-card-top"><CompanyLogo job={job} /><div><p className="company-name">{job.company}</p><span className="muted small">{job.location || "Location not specified"}</span></div>{match && <span className="match-score">{Math.round(match.final_score * 100)}<small>/100</small></span>}</div>
    {selection}
    <h3><Link href={`/jobs/${job.id}${match ? `?match=${match.id}` : ""}`}>{job.title}</Link></h3>
    <div className="chips">{job.required_skills.slice(0, 4).map(skill => <Badge key={skill}>{skill}</Badge>)}</div>
    {match && <p className="small muted">{match.method === "sbert" ? "SBERT + structured signals" : `${match.method === "tfidf" ? "TF-IDF" : "Keyword"} baseline + structured signals`}</p>}
    <div className="job-card-footer"><span className="small muted">{job.ats || "Job posting"}</span><Link className="inline-link" href={`/jobs/${job.id}${match ? `?match=${match.id}` : ""}`}>View opportunity <span aria-hidden>↗</span></Link></div></article>;
}
export function Pagination({ offset, total, size = 12, onChange }: { offset: number; total: number; size?: number; onChange: (offset: number) => void }) {
  return <div className="pagination"><span className="muted small">{total ? `${offset + 1}–${Math.min(offset + size, total)} of ${total.toLocaleString()}` : "0 results"}</span><div><button className="button secondary small" disabled={offset === 0} onClick={() => onChange(Math.max(0, offset - size))}>Previous</button><button className="button secondary small" disabled={offset + size >= total} onClick={() => onChange(offset + size)}>Next</button></div></div>;
}
