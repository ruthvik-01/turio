import { LandingActions } from "@/components/ui";

export default function Landing() {
  return <main className="container landing">
    <section className="landing-hero"><div><h1><span>Jobs and applications,</span><span className="hero-last-line">in one place.</span></h1>
      <LandingActions /></div>
    </section>
  </main>;
}
