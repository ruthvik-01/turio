"use client";
import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import type { Education, Experience, Profile, Project } from "@/lib/types";
import { useSession } from "./session";
import { Loading, Notice, PageHeading, Workspace } from "./ui";

const blankExperience: Experience = { company: "", title: "", start_date: null, end_date: null, description: "" };
const blankEducation: Education = { institution: "", degree: "", field: "", start_date: null, end_date: null };
const blankProject: Project = { name: "", description: "", technologies: [] };
const split = (value: string) => [...new Set(value.split(",").map(s => s.trim()).filter(Boolean))];

export function ProfileEditor({ onboarding = false }: { onboarding?: boolean }) {
  const { user } = useSession();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [skills, setSkills] = useState(""); const [roles, setRoles] = useState("");
  const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [notice, setNotice] = useState("");
  const [file, setFile] = useState<File | null>(null);
  function populate(p: Profile) { setProfile(p); setSkills(p.skills.map(s => s.name).join(", ")); setRoles((p.preferred_roles || []).join(", ")); }
  useEffect(() => { if (user) api<Profile>("/profiles/me").then(populate).catch(error => setError(error.message)); }, [user]);
  function update(key: keyof Profile, value: unknown) { setProfile(p => p ? { ...p, [key]: value } : p); setNotice(""); }
  function choose(selected?: File) {
    if (!selected) return;
    if (!(selected.type === "application/pdf" || ((!selected.type || selected.type === "application/octet-stream") && /\.pdf$/i.test(selected.name))) || selected.size > 5 * 1024 * 1024) { setFile(null); setError("Choose a PDF of 5 MB or less."); return; }
    setFile(selected); setError("");
  }
  async function upload() {
    if (!file) return;
    setBusy(true); setError(""); setNotice("Extracting your resume. Review the results before continuing.");
    try {
      const data = new FormData(); data.append("file", file);
      const result = await api<{ profile: Profile; reprocessed: boolean }>("/resumes", { method: "POST", body: data });
      populate(result.profile); setFile(null); setNotice(result.reprocessed ? "Resume extracted. Check and correct the details below." : "This resume was already processed. Your stored profile has been loaded.");
    } catch (error) { setError((error as Error).message); setNotice(""); } finally { setBusy(false); }
  }
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!profile) return; setBusy(true); setError(""); setNotice("");
    const { id, version, skills: _, ...values } = profile;
    try {
      populate(await api<Profile>("/profiles/me", { method: "PATCH", body: JSON.stringify({ ...values, projects: values.projects.map(project => ({ ...project, technologies: split(project.technologies.join(",")) })), skills: split(skills), preferred_roles: split(roles) }) }));
      setNotice("Profile saved. Recommendations and application reviews will use this updated version.");
    } catch (error) { setError((error as Error).message); } finally { setBusy(false); }
  }
  return <Workspace><PageHeading eyebrow={onboarding ? "First, your story" : "Your reusable profile"} title={onboarding ? "Let’s get to know you." : "Make it your own."} action={<Link className="button secondary small" href="/home">Back to workspace</Link>}>A little care here means less repetition in every application.</PageHeading>
    {error && <Notice kind="error">{error}</Notice>}{notice && <Notice kind={busy ? "info" : "success"}>{notice}</Notice>}
    <section className="panel form-panel"><h2>Start with your resume</h2><p className="muted">PDF only, up to 5 MB. A new resume replaces the parsed profile fields below; review any existing corrections before uploading.</p>
      <div className="upload" onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); if (!busy) choose(e.dataTransfer.files[0]); }}>
        <span className="empty-mark" aria-hidden>↑</span><h3>{file ? file.name : "Drop your resume here"}</h3><p className="small muted">or choose a file from your computer</p><label><span className="small">Choose PDF resume</span><input type="file" accept="application/pdf" disabled={busy} onChange={e => choose(e.target.files?.[0])} /></label>
        <button className="button primary" style={{ marginTop: 18 }} disabled={!file || busy} onClick={upload}>{busy ? "Working…" : "Upload & extract"}</button></div></section>
    {!profile ? !error && <Loading /> : <form onSubmit={save}>
      <section className="panel form-panel"><h2>The essentials</h2><p className="muted">Only include information you want to reuse in applications. Your account email is {user?.email}.</p><div className="form-grid">
        {([["full_name", "Full name", "text"], ["phone", "Phone number", "tel"], ["location", "Current location", "text"], ["linkedin_url", "LinkedIn URL", "url"], ["github_url", "GitHub URL", "url"], ["portfolio_url", "Portfolio URL", "url"]] as const).map(([key, label, type]) => <label key={key}>{label}<input type={type} value={profile[key] || ""} onChange={e => update(key, e.target.value || null)} /></label>)}
        <label className="span-two">Preferred roles<input value={roles} placeholder="Backend engineer, Software developer" onChange={e => setRoles(e.target.value)} /><span className="small muted">Separate roles with commas.</span></label>
        <label className="span-two">Skills<input value={skills} placeholder="Python, FastAPI, PostgreSQL" onChange={e => setSkills(e.target.value)} /><span className="small muted">Separate skills with commas. These become matching evidence.</span></label>
      </div></section>
      <section className="panel form-panel"><h2>Experience</h2><p className="muted">Keep titles, dates, and descriptions accurate. Leave the end date blank for a current role.</p>
        {profile.experiences.map((item, i) => <div className="entity" key={i}><div className="form-grid">{(["company", "title", "start_date", "end_date", "description"] as const).map(key => <label className={key === "description" ? "span-two" : ""} key={key}>{key.replaceAll("_", " ")}{key === "description" ? <textarea value={item[key] || ""} onChange={e => update("experiences", profile.experiences.map((x, j) => j === i ? { ...x, [key]: e.target.value || null } : x))} /> :
          <input type={key.includes("date") ? "date" : "text"} value={item[key] || ""} onChange={e => update("experiences", profile.experiences.map((x, j) => j === i ? { ...x, [key]: e.target.value || null } : x))} />}</label>)}</div><button className="text-button" type="button" onClick={() => update("experiences", profile.experiences.filter((_, j) => i !== j))}>Remove experience</button></div>)}
        <button className="button secondary small" type="button" onClick={() => update("experiences", [...profile.experiences, { ...blankExperience }])}>+ Add experience</button></section>
      <section className="panel form-panel"><h2>Education</h2>{profile.educations.map((item, i) => <div className="entity" key={i}><div className="form-grid">{(["institution", "degree", "field", "start_date", "end_date"] as const).map(key => <label key={key}>{key.replaceAll("_", " ")}<input type={key.includes("date") ? "date" : "text"} value={item[key] || ""} onChange={e => update("educations", profile.educations.map((x, j) => j === i ? { ...x, [key]: e.target.value || null } : x))} /></label>)}</div><button className="text-button" type="button" onClick={() => update("educations", profile.educations.filter((_, j) => i !== j))}>Remove education</button></div>)}
        <button className="button secondary small" type="button" onClick={() => update("educations", [...profile.educations, { ...blankEducation }])}>+ Add education</button></section>
      <section className="panel form-panel"><h2>Projects</h2>{profile.projects.map((item, i) => <div className="entity" key={i}><div className="form-grid"><label>Project name<input value={item.name || ""} onChange={e => update("projects", profile.projects.map((x, j) => j === i ? { ...x, name: e.target.value || null } : x))} /></label><label>Technologies<input value={item.technologies.join(", ")} onChange={e => update("projects", profile.projects.map((x, j) => j === i ? { ...x, technologies: e.target.value.split(",") } : x))} /></label><label className="span-two">Description<textarea value={item.description || ""} onChange={e => update("projects", profile.projects.map((x, j) => j === i ? { ...x, description: e.target.value || null } : x))} /></label></div><button className="text-button" type="button" onClick={() => update("projects", profile.projects.filter((_, j) => i !== j))}>Remove project</button></div>)}
        <button className="button secondary small" type="button" onClick={() => update("projects", [...profile.projects, { ...blankProject }])}>+ Add project</button></section>
      <section className="panel form-panel"><h2>Application preferences</h2><p className="muted">These are your explicit answers—not assumptions from your resume. Leave them blank if the answer depends on the country or role.</p><div className="form-grid"><label>Work authorization status<input value={profile.work_authorization_status || ""} onChange={e => update("work_authorization_status", e.target.value || null)} placeholder="Optional; include the relevant country" /></label><label>Do you require sponsorship?<select value={profile.sponsorship_required === null ? "" : String(profile.sponsorship_required)} onChange={e => update("sponsorship_required", e.target.value === "" ? null : e.target.value === "true")}><option value="">Not specified / depends on role</option><option value="true">Yes</option><option value="false">No</option></select></label></div></section>
      <div className="actions"><button className="button primary" disabled={busy}>{busy ? "Saving…" : "Save profile"}</button><Link className="button secondary" href="/jobs">Explore opportunities ↗</Link><span className="small muted">Profile version {profile.version}</span></div>
    </form>}
  </Workspace>;
}
