import { LandingActions } from "@/components/ui";

export default function Landing() {
  return <main className="container landing">
    <section className="landing-hero"><div><h1><span>Jobs and applications,</span><span className="hero-last-line">in one place.</span></h1>
      <p className="hero-copy">Search jobs, reuse your resume and keep track of your applications.</p>
      <LandingActions />
      <p className="small muted hero-footnote">Review your answers before submitting. You choose when to apply.</p></div>
    </section>
  </main>;
}
