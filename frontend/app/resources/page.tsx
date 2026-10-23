import Link from "next/link";
import { PageHeading, Workspace } from "@/components/ui";
export default function Page() {
  return <Workspace><PageHeading eyebrow="" title="Resources">How profiles, recommendations and application preparation work.</PageHeading><div className="three-column resource-grid">
    <article className="panel"><h2>Profile details</h2><p>PDF extraction uses conservative rules. Review your name, dates, skills, and projects. Unknown information stays blank, and sensitive declarations are never inferred.</p><Link className="button secondary small" style={{ marginTop: 24 }} href="/profile">Review profile ↗</Link></article>
    <article className="panel"><h2>Job recommendations</h2><p>Recommendations use SBERT, a local semantic model, to compare your profile with each job. The text score is combined with available structured evidence such as skills, location and experience. Scores are not hiring probabilities.</p><Link className="button secondary small" style={{ marginTop: 24 }} href="/jobs">Explore opportunities ↗</Link></article>
    <article className="panel"><h2>Application preparation</h2><p>Browser assistance is experimental and stops on unsupported forms or uncertain results. Preparation never submits. Final submission requires explicit approval of an unchanged review. Manual submissions are labeled separately.</p><Link className="button secondary small" style={{ marginTop: 24 }} href="/applications">View applications ↗</Link></article>
  </div></Workspace>;
}
