"use client";
import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import type { Education, Experience, Profile, Project, ResumeMeta, ResumeSuggestions } from "@/lib/types";
import { useSession } from "./session";
import { Loading, Notice, PageHeading, Workspace } from "./ui";
import { Select } from "./select";

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
  const fileInput = useRef<HTMLInputElement>(null);
  const [savedProfile, setSavedProfile] = useState<Profile | null>(null);
  const [resume, setResume] = useState<ResumeMeta | null>(null);
  const [aiConsent, setAiConsent] = useState(false);
  const [suggestions, setSuggestions] = useState<ResumeSuggestions | null>(null);
  const [dirty, setDirty] = useState(false);
  const [formKey, setFormKey] = useState(0);
  const dirtyRef = useRef(false);
  const resumeRef = useRef<ResumeMeta | null>(null);
  function selectResume(value: ResumeMeta | null) { resumeRef.current = value; setResume(value); setSuggestions(null); setAiConsent(false); }
  function markDirty() { dirtyRef.current = true; setDirty(true); }
  function populate(p: Profile) { setProfile(p); setSavedProfile(p); setSkills(p.skills.map(s => s.name).join(", ")); setRoles((p.preferred_roles || []).join(", ")); dirtyRef.current = false; setDirty(false); setSuggestions(null); setFormKey(k => k + 1); }
  useEffect(() => { if (user) Promise.all([api<Profile>("/profiles/me"), api<ResumeMeta | null>("/resumes/latest")]).then(([p, r]) => { populate(p); selectResume(r); }).catch(error => setError(error.message)); }, [user]);
  function update(key: keyof Profile, value: unknown) { markDirty(); setProfile(p => p ? { ...p, [key]: value } : p); setNotice(""); }
  function choose(selected?: File) {
    setSuggestions(null); setAiConsent(false);
    if (!selected) { setFile(null); return; }
    if (!(selected.type === "application/pdf" || ((!selected.type || selected.type === "application/octet-stream") && /\.pdf$/i.test(selected.name))) || selected.size > 5 * 1024 * 1024) { setFile(null); setError("Choose a PDF of 5 MB or less."); return; }
    setFile(selected); setError("");
  }
  async function upload() {
    if (!file) return;
    if (profile && (dirty || profile.version > 1) && !window.confirm("Uploading a new resume will replace your current profile details and manual edits. Continue?")) return;
    setBusy(true); setError(""); setNotice("Extracting your resume. Review the results before continuing.");
    try {
      const data = new FormData(); data.append("file", file);
      const result = await api<{ profile: Profile; resume: ResumeMeta; reprocessed: boolean }>("/resumes", { method: "POST", body: data });
      populate(result.profile); selectResume(result.resume); setFile(null); if (fileInput.current) fileInput.current.value = ""; setNotice(result.reprocessed ? "Resume extracted. Check and correct the details below." : "This resume was already processed. Your stored profile has been loaded.");
    } catch (error) { setError((error as Error).message); setNotice(""); } finally { setBusy(false); }
  }
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!profile) return; setBusy(true); setError(""); setNotice("");
    const { id, version, skills: _, ...values } = profile;
    try {
      populate(await api<Profile>("/profiles/me", { method: "PATCH", body: JSON.stringify({ ...values, expected_profile_version: version, projects: values.projects.map(project => ({ ...project, technologies: split(project.technologies.join(",")) })), skills: split(skills), preferred_roles: split(roles) }) }));
      setNotice("Profile saved. Recommendations and application reviews will use this updated version.");
    } catch (error) { setError((error as Error).message); } finally { setBusy(false); }
  }
  async function requestSuggestions() {
    if (!resume || !aiConsent || dirtyRef.current) return;
    setBusy(true); setError(""); setSuggestions(null);
    try { setSuggestions(await api<ResumeSuggestions>(`/resumes/${resume.id}/suggestions`, { method: "POST", body: JSON.stringify({ consent: true }) })); }
    catch (error) { setError((error as Error).message); }
    finally { setBusy(false); setAiConsent(false); }
  }
  async function acceptSuggestions() {
    if (!suggestions || !profile || dirtyRef.current) return;
    setBusy(true); setError("");
    try {
      const current = await api<Profile>("/profiles/me");
      if (dirtyRef.current || resumeRef.current?.id !== suggestions.resume_id || resumeRef.current?.checksum !== suggestions.resume_checksum
          || current.version !== suggestions.profile_version || profile.version !== suggestions.profile_version) {
        setSuggestions(null); throw new Error("Your resume or profile changed. Reload the profile and request fresh suggestions.");
      }
      const { skills: proposedSkills, ...entities } = suggestions.suggested_fields;
      setProfile({ ...profile, ...entities, ...(proposedSkills ? { skills: proposedSkills.map(name => ({ name, normalized_name: name.toLowerCase() })) } : {}) });
      if (proposedSkills) setSkills(proposedSkills.join(", "));
      markDirty(); setFormKey(k => k + 1); setSuggestions(null); setNotice("Suggested changes are in the editor. Review them, then save your profile.");
    } catch (error) { setError((error as Error).message); }
    finally { setBusy(false); }
  }
  return <Workspace><PageHeading eyebrow="" title={onboarding ? "Set up your profile" : "Profile"} action={<Link className="button secondary small" href="/home">Back to home</Link>}>Check the information you want to reuse in applications.</PageHeading>
    {error && <Notice kind="error">{error}</Notice>}{notice && <Notice kind={busy ? "info" : "success"}>{notice}</Notice>}
    <section className="panel form-panel"><h2>Start with your resume</h2><p className="muted">Text-based PDF only, up to 5 MB and 30 pages. Local extraction handles page and column layouts; scanned pages need searchable text first. A new resume replaces the parsed fields below; review existing corrections before uploading.</p>
      <div className="resume-upload">
        <label>Choose PDF resume<input ref={fileInput} type="file" accept="application/pdf,.pdf" disabled={busy} onChange={e => choose(e.target.files?.[0])} /></label>
        <button className="button primary" disabled={!file || busy} onClick={upload}>{busy ? "Extracting…" : "Upload resume"}</button>
      </div><p className="small muted" style={{ marginTop: 12 }}>Upload once. Your saved resume is reused in application preparation.</p></section>
    <section className="panel form-panel"><h2>Optional resume assistance</h2>
      <p className="muted">OpenRouter can interpret sections, job titles, companies, degrees and project boundaries from your extracted resume text. Local parsing remains the fallback for incomplete or unavailable decisions. No Google service is used. This sends bounded section text and nearby excerpts through OpenRouter to the configured free model. Excerpts may contain personal information and may be retained under its terms. Your PDF file is not sent.</p>
      {resume && <p className="small">Selected resume: {resume.original_filename}</p>}
      {dirty && <Notice>Save or discard your unsaved edits before requesting or accepting suggestions.</Notice>}
      {dirty && <button className="button secondary small" disabled={busy} onClick={() => { if (savedProfile) populate(savedProfile); }}>Discard unsaved edits</button>}
      <label className="check-label"><input type="checkbox" checked={aiConsent} disabled={busy || dirty || !!file} onChange={e => setAiConsent(e.target.checked)} />I agree to send these excerpts to the external AI service for this action.</label>
      <button className="button secondary" disabled={busy || dirty || !!file || !resume || !aiConsent} onClick={requestSuggestions}>Interpret resume with AI</button>
      {suggestions && <div style={{ marginTop: 16 }}>
        {suggestions.status === "unavailable" && <Notice>AI assistance unavailable. Local parsing and editing remain available.</Notice>}
        {suggestions.status === "stale" && <Notice>These suggestions are stale. Reload your profile and try again.</Notice>}
        {suggestions.status === "ocr_needed" && <Notice>This PDF has no readable text. A scanned resume needs OCR before section assistance.</Notice>}
        <p className="small muted">Model: {suggestions.model} · {suggestions.provider || "legacy provider"}. {suggestions.unresolved} unresolved source decisions; {suggestions.overflow} candidates outside the assistance limits. Decision confidence is not verified accuracy.</p>
        {suggestions.suggestions.map(s => <div className="entity" key={s.id}><strong>{s.heading} → {s.section}</strong>{s.uncertain && <Notice>Uncertain suggestion: verify the source before accepting.</Notice>}<p className="small muted">{s.confidence != null && s.winner_probability != null ? <>Decision confidence {(s.confidence * 100).toFixed(0)}%; winner probability {(s.winner_probability * 100).toFixed(0)}%.</> : "Confidence/probability scores are unavailable. Verify this source-based classification before accepting."}</p><pre style={{ whiteSpace: "pre-wrap" }}>{s.excerpt}</pre></div>)}
        {suggestions.suggested_fields.skills && <p>Proposed skills: {suggestions.suggested_fields.skills.join(", ")}</p>}
        {suggestions.suggested_fields.experiences?.map((e, i) => <p key={`exp-${i}`}>Proposed experience: {e.title} · {e.company} · {e.start_date || "Date not found"}–{e.end_date || "No end date found"}</p>)}
        {suggestions.suggested_fields.educations?.map((e, i) => <p key={`edu-${i}`}>Proposed education: {e.degree} · {e.institution}</p>)}
        {suggestions.suggested_fields.projects?.map((p, i) => <p key={`proj-${i}`}>Proposed project: {p.name} · {p.description}</p>)}
        {suggestions.suggested_fields.summary && <p>Proposed summary: {suggestions.suggested_fields.summary}</p>}
        {suggestions.suggested_fields.certifications?.map((value, i) => <p key={`cert-${i}`}>Proposed certification: {value}</p>)}
        {suggestions.suggested_fields.achievements?.map((value, i) => <p key={`award-${i}`}>Proposed achievement: {value}</p>)}
        {Object.keys(suggestions.suggested_fields).length > 0 && <button className="button secondary" disabled={busy || dirty} onClick={acceptSuggestions}>Use suggested changes in editor</button>}
      </div>}
    </section>
    {!profile ? !error && <Loading /> : <form onSubmit={save}>
      <section className="panel form-panel"><h2>The essentials</h2><p className="muted">Only include information you want to reuse in applications. Your account email is {user?.email}.</p><div className="form-grid">
        {([["full_name", "Full name", "text"], ["contact_email", "Application email (does not change login)", "email"], ["phone", "Phone number", "tel"], ["location", "Current location", "text"], ["linkedin_url", "LinkedIn URL", "url"], ["github_url", "GitHub URL", "url"], ["portfolio_url", "Portfolio URL", "url"]] as const).map(([key, label, type]) => <label key={key}>{label}<input type={type} value={profile[key] || ""} onChange={e => update(key, e.target.value || null)} /></label>)}
        <label className="span-two">Preferred roles<input value={roles} placeholder="Backend engineer, Software developer" onChange={e => { markDirty(); setRoles(e.target.value); }} /><span className="small muted">Separate roles with commas.</span></label>
        <label className="span-two">Skills<input value={skills} placeholder="Python, FastAPI, PostgreSQL" onChange={e => { markDirty(); setSkills(e.target.value); }} /><span className="small muted">Separate skills with commas. These become matching evidence.</span></label>
      </div></section>
      <section className="panel form-panel"><h2>Experience</h2><p className="muted">Keep titles, dates, and descriptions accurate. Leave the end date blank for a current role.</p>
        {profile.experiences.map((item, i) => <div className="entity" key={i}><div className="form-grid">{(["company", "title", "start_date", "end_date", "description"] as const).map(key => <label className={key === "description" ? "span-two" : ""} key={key}>{key.replaceAll("_", " ")}{key === "description" ? <textarea value={item[key] || ""} onChange={e => update("experiences", profile.experiences.map((x, j) => j === i ? { ...x, [key]: e.target.value || null } : x))} /> :
          <input type={key.includes("date") ? "date" : "text"} value={item[key] || ""} onChange={e => update("experiences", profile.experiences.map((x, j) => j === i ? { ...x, [key]: e.target.value || null } : x))} />}</label>)}</div><button className="text-button" type="button" onClick={() => update("experiences", profile.experiences.filter((_, j) => i !== j))}>Remove experience</button></div>)}
        <button className="button secondary small" type="button" onClick={() => update("experiences", [...profile.experiences, { ...blankExperience }])}>+ Add experience</button></section>
      <section className="panel form-panel"><h2>Education</h2>{profile.educations.map((item, i) => <div className="entity" key={i}><div className="form-grid">{(["institution", "degree", "field", "start_date", "end_date"] as const).map(key => <label key={key}>{key.replaceAll("_", " ")}<input type={key.includes("date") ? "date" : "text"} value={item[key] || ""} onChange={e => update("educations", profile.educations.map((x, j) => j === i ? { ...x, [key]: e.target.value || null } : x))} /></label>)}</div><button className="text-button" type="button" onClick={() => update("educations", profile.educations.filter((_, j) => i !== j))}>Remove education</button></div>)}
        <button className="button secondary small" type="button" onClick={() => update("educations", [...profile.educations, { ...blankEducation }])}>+ Add education</button></section>
      <section className="panel form-panel"><h2>Projects</h2>{profile.projects.map((item, i) => <div className="entity" key={i}><div className="form-grid"><label>Project name<input value={item.name || ""} onChange={e => update("projects", profile.projects.map((x, j) => j === i ? { ...x, name: e.target.value || null } : x))} /></label><label>Technologies<input key={`tech-${formKey}-${i}`} defaultValue={item.technologies.join(", ")} onChange={e => update("projects", profile.projects.map((x, j) => j === i ? { ...x, technologies: e.target.value.split(",") } : x))} /></label><label className="span-two">Description<textarea value={item.description || ""} onChange={e => update("projects", profile.projects.map((x, j) => j === i ? { ...x, description: e.target.value || null } : x))} /></label></div><button className="text-button" type="button" onClick={() => { setFormKey(k => k + 1); update("projects", profile.projects.filter((_, j) => i !== j)); }}>Remove project</button></div>)}
        <button className="button secondary small" type="button" onClick={() => update("projects", [...profile.projects, { ...blankProject }])}>+ Add project</button></section>
      <section className="panel form-panel"><h2>Summary and credentials</h2><div className="form-grid">
        <label className="span-two">Professional summary<textarea maxLength={10000} value={profile.summary || ""} onChange={e => update("summary", e.target.value || null)} /></label>
        {(["certifications", "achievements"] as const).map(key => <label className="span-two" key={key}>{key === "certifications" ? "Certifications" : "Achievements"}<textarea value={(profile[key] || []).join("\n")} onChange={e => update(key, e.target.value.split("\n"))} onBlur={() => update(key, (profile[key] || []).map(value => value.trim()).filter(Boolean))} /><span className="small muted">One source-backed fact per line. Review before saving.</span></label>)}
      </div></section>
      <section className="panel form-panel"><h2>Application preferences</h2><p className="muted">You provide these answers. They are not inferred from your resume. Leave them blank if the answer depends on the country or role.</p><div className="form-grid"><label>Work authorization status<input value={profile.work_authorization_status || ""} onChange={e => update("work_authorization_status", e.target.value || null)} placeholder="Optional; include the relevant country" /></label><label>Do you require sponsorship?<Select label="Do you require sponsorship?" value={profile.sponsorship_required === null ? "" : String(profile.sponsorship_required)} onChange={value => update("sponsorship_required", value === "" ? null : value === "true")} placeholder="Not specified / depends on role" options={[{ value: "", label: "Not specified / depends on role" }, { value: "true", label: "Yes" }, { value: "false", label: "No" }]} /></label></div></section>
      <div className="actions"><button className="button primary" disabled={busy}>{busy ? "Saving…" : "Save profile"}</button><Link className="button secondary" href="/jobs">Explore opportunities ↗</Link><span className="small muted">Profile version {profile.version}</span></div>
    </form>}
  </Workspace>;
}
