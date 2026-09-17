import Link from "next/link";
import { GrowthArt } from "@/components/growth-art";

export default function Landing() {
  return <main className="container landing">
    <section className="landing-hero"><div><p className="eyebrow">A more thoughtful job search</p><h1>Your next chapter.<br /><em>A little closer.</em></h1>
      <p className="hero-copy">Bring your experience. Find opportunities that fit. Keep every application in one calm, organized space.</p>
      <div className="actions"><Link className="button primary" href="/signup">Find your next step <span aria-hidden>↗</span></Link><Link className="button secondary" href="/login">I already have an account</Link></div>
      <p className="small muted hero-footnote">Your profile stays yours. You decide when to apply.</p></div><GrowthArt />
    </section>
    <section className="journey" aria-labelledby="journey-title"><div><p className="eyebrow">Less repetition. More intention.</p><h2 id="journey-title">Make space for what’s next.</h2></div>
      <div className="three-column">{[
        ["01", "Start with your story", "Upload a PDF resume, review the extracted details, and build a profile you can keep using."],
        ["02", "Find a considered fit", "Explore the job inventory and compare recommendations with visible evidence—not hidden promises."],
        ["03", "Move at your pace", "Prepare your answers, review every detail, and track what happens next. Submission is always your decision."],
      ].map(([number, title, copy]) => <article className="step-card" key={number}><span>{number}</span><h3>{title}</h3><p>{copy}</p></article>)}</div>
    </section>
  </main>;
}
