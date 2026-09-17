import Link from "next/link";
import { PageHeading, Workspace } from "@/components/ui";
export default function Page() {
  return <Workspace><PageHeading eyebrow="A little clarity" title="Make the most of Turio.">Know what the system does—and where your judgment comes first.</PageHeading><div className="three-column resource-grid">
    <article className="panel"><p className="eyebrow">01 · Your profile</p><h2>Keep the evidence accurate.</h2><p>PDF extraction uses conservative rules. Review your name, dates, skills, and projects. Unknown information stays blank, and sensitive declarations are never inferred.</p><Link className="button secondary small" style={{ marginTop: 24 }} href="/profile">Review profile ↗</Link></article>
    <article className="panel"><p className="eyebrow">02 · Recommendations</p><h2>A score is a starting point.</h2><p>Keyword and TF-IDF are labeled baselines. SBERT requires a configured local model. All methods combine text relevance with available structured evidence. Scores are not hiring probabilities.</p><Link className="button secondary small" style={{ marginTop: 24 }} href="/jobs">Explore opportunities ↗</Link></article>
    <article className="panel"><p className="eyebrow">03 · Applications</p><h2>You make the final call.</h2><p>Browser assistance is experimental and stops on unsupported forms or uncertain results. Preparation never submits. Final submission requires explicit approval of an unchanged review. Manual submissions are labeled separately.</p><Link className="button secondary small" style={{ marginTop: 24 }} href="/applications">View applications ↗</Link></article>
  </div></Workspace>;
}
