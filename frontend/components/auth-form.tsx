"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";
import { useSession } from "./session";
import { Notice } from "./ui";

export function AuthForm({ signup = false }: { signup?: boolean }) {
  const router = useRouter();
  const { setUser } = useSession();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    const data = new FormData(event.currentTarget);
    try {
      const result = await api<{ user: User }>(`/auth/${signup ? "register" : "login"}`, { method: "POST", body: JSON.stringify({ email: data.get("email"), password: data.get("password") }) });
      setUser(result.user); router.push(signup ? "/onboarding" : "/home");
    } catch (error) { setError((error as Error).message); } finally { setBusy(false); }
  }
  return <main className="auth-layout container"><section className="auth-intro"><p className="eyebrow">Your next chapter</p><h1>{signup ? <>A fresh start.<br /><em>On your terms.</em></> : <>Welcome back.<br /><em>Let’s keep going.</em></>}</h1><p>A thoughtful place to find opportunities, prepare applications, and see how far you’ve come.</p></section>
    <section className="panel auth-card"><h2>{signup ? "Create your workspace" : "Sign in to Turio"}</h2><p className="muted">{signup ? "Start with an account. Add your story next." : "Your progress is right where you left it."}</p>
      {error && <Notice kind="error">{error}</Notice>}<form onSubmit={submit}><label>Email address<input name="email" type="email" autoComplete="email" placeholder="you@example.com" required /></label><label>Password<input name="password" type="password" autoComplete={signup ? "new-password" : "current-password"} minLength={signup ? 8 : 1} required /></label>
        {signup && <p className="small muted">At least 8 characters; up to 72 UTF-8 bytes.</p>}<button className="button primary full" disabled={busy}>{busy ? "Please wait…" : signup ? "Create account ↗" : "Sign in ↗"}</button></form>
      <p className="auth-switch">{signup ? "Already have an account?" : "New here?"} <Link href={signup ? "/login" : "/signup"}>{signup ? "Sign in" : "Create an account"}</Link></p></section></main>;
}
