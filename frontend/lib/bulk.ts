import type { Application, Field } from "./types";

export function sharedQuestionKey(field: Field): string | null {
  if (field.input_type === "file" || (field.input_type === "checkbox" && field.required)) return null;
  if (["full_name", "email", "phone", "location", "linkedin_url", "github_url", "portfolio_url"].includes(field.normalized_intent)
      && ["text", "email", "tel", "url"].includes(field.input_type)) return JSON.stringify(["contact_fact", field.normalized_intent]);
  const label = field.label.toLowerCase().replaceAll("résumé", "resume").replace(/[^a-z0-9 ]/g, " ").trim().replace(/\s+/g, " ");
  return JSON.stringify([label, field.input_type, field.options]);
}

export function automaticBlocker(app: Application): string | null {
  if (app.status === "submitted") return "Already submitted.";
  if (app.manual_submission_required !== false) return "Manual final submission required.";
  if (app.status !== "ready_for_review") return "Preparation or review is still needed.";
  if (!app.resume_id) return "A stored resume is required.";
  if (app.missing_fields.length || !app.fields.length) return "Required answers are missing or unconfirmed.";
  if (app.fields.some(field => field.required && (!field.user_confirmed || field.value === null || (Array.isArray(field.value) && !field.value.length) || (typeof field.value === "string" && !field.value.trim())
      || (field.input_type === "checkbox" && field.value !== true)))) return "Required answers are missing or unconfirmed.";
  if (app.fields.some(field => field.input_type === "file" && field.value && field.value !== app.resume_id)) return "The resume selection changed.";
  return null;
}

export function approvalFingerprint(app: Application): string {
  return JSON.stringify({ application_id: app.id, job_id: app.job.id, job_title: app.job.title, company: app.job.company, application_url: app.application_url, resume_id: app.resume_id,
    profile_version: app.profile_version,
    fields: app.fields.map(field => ({ key: field.field_key, label: field.label, type: field.input_type,
      required: field.required, options: field.options, help_text: field.help_text,
      value: field.value, source: field.value_source, confirmed: field.user_confirmed }))
      .sort((a, b) => a.key.localeCompare(b.key)) });
}

export function batchApprovalFresh(started: number, now = Date.now()): boolean {
  return now >= started && now - started <= 15 * 60 * 1000;
}

export function filledValue(field: Field): string {
  if (field.value === null || field.value === "") return "Not provided";
  if (field.input_type === "file") return "Stored original resume";
  if (typeof field.value === "boolean") return field.value ? "Yes" : "No";
  if (Array.isArray(field.value)) return field.value.map(value=>field.options.find(option=>option.value===value)?.label || value).join(", ");
  if (field.input_type === "select") return field.options.find(option => option.value === field.value)?.label || String(field.value);
  return String(field.value);
}
