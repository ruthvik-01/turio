export type User = { id: string; email: string };
export type Experience = { company: string | null; title: string | null; start_date: string | null; end_date: string | null; description: string | null };
export type Education = { institution: string | null; degree: string | null; field: string | null; start_date: string | null; end_date: string | null };
export type Project = { name: string | null; description: string | null; technologies: string[] };
export type Profile = {
  id: string; version: number; full_name: string | null; phone: string | null; location: string | null;
  contact_email: string | null; summary: string | null; certifications: string[] | null; achievements: string[] | null;
  linkedin_url: string | null; github_url: string | null; portfolio_url: string | null;
  preferred_roles: string[] | null; work_authorization_status: string | null; sponsorship_required: boolean | null;
  skills: { name: string; normalized_name: string }[]; experiences: Experience[]; educations: Education[]; projects: Project[];
};
export type ResumeMeta = { id: string; checksum: string; original_filename: string };
export type ResumeSuggestions = {
  resume_id: string; resume_checksum: string; profile_version: number; model: string; provider?: string; status: string;
  overflow: number; unresolved: number;
  suggestions: { id: string; heading: string; excerpt: string; section: string; confidence: number | null; winner_probability: number | null; uncertain?: boolean }[];
  suggested_fields: { skills?: string[]; experiences?: Experience[]; educations?: Education[]; projects?: Project[]; summary?: string | null; certifications?: string[]; achievements?: string[] };
};
export type Job = { id: string; title: string; company: string; description: string | null; location: string | null; job_url: string; application_url: string | null; ats: string | null; required_skills: string[]; company_logo_url?: string | null; application_deadline?: string | null };
export type JobPage = { jobs: Job[]; total: number; limit: number; offset: number };
export type Method = "keyword" | "tfidf" | "sbert";
export type Match = { id: string; job: Job; method: Method; final_score: number; model_name: string; explanation: { summary: string; disclaimer: string; matched_skills: string[]; missing_skills: string[]; scores: Record<string, number | null> } };
export type MatchPage = { matches: Match[]; total: number; stale: boolean };
export type Field = { id: string; field_key: string; label: string; input_type: string; required: boolean; normalized_intent: string; options: { value: string; label: string }[]; help_text?: string | null; value: string | boolean | string[] | null; value_source: string; user_confirmed: boolean; ai_confidence?: number | null; ai_winner_probability?: number | null; ai_uncertain?: boolean };
export type Application = {
  id: string; job: Job; application_url: string; status: string; outcome: string | null; notes: string | null;
  resume_id: string | null; revision: number;
  profile_version?: number | null;
  manual_submission_required?: boolean;
  fields: Field[]; missing_fields: string[]; review_token: string | null; reviewed_at?: string | null; readiness_score: number;
  submission_method: string | null; submitted_at: string | null; created_at: string;
  events: { event_type: string; event_data: Record<string, unknown>; created_at: string }[];
};
export type ApplicationPage = { applications: Application[]; total: number };
export type Summary = { total: number; interviews: number; offers: number; in_progress: number; submitted: number; cancelled: number; needs_attention?: number; days: { date: string; count: number }[] };
export type Run = {
  id: string; kind: "jobs_refresh" | "matches_refresh";
  state: "queued" | "running" | "succeeded" | "failed" | "interrupted" | "cancelled";
  result: unknown; error_code: string | null; error_message: string | null;
};
