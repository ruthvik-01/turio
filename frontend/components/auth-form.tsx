"use client";
import { ButtonLabel, TransitionLink as Link, useImmediateNavigation } from "./route-motion";
import { useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";
import { useSession } from "./session";
import { Notice } from "./ui";

export function AuthForm({ signup = false }: { signup?: boolean }) {
  const navigate = useImmediateNavigation();
  const { setUser } = useSession();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    const data = new FormData(event.currentTarget);
    try {
      const result = await api<{ user: User }>(`/auth/${signup ? "register" : "login"}`, { method: "POST", body: JSON.stringify({ email: data.get("email"), password: data.get("password") }) });
      setUser(result.user); navigate(signup ? "/onboarding" : "/home");
    } catch (error) { setError((error as Error).message); } finally { setBusy(false); }
  }
  return <main className="auth-layout container"><section className="auth-intro"><h1>{signup ? "Create account" : "Sign in"}</h1><p>{signup ? "Save your profile and track your applications." : "Open your saved jobs and applications."}</p></section>
    <section className="panel auth-card"><h2>{signup ? "Your account" : "Account details"}</h2><p className="muted">{signup ? "Use your email address to create an account." : "Enter your email address and password."}</p>
      {error && <Notice kind="error">{error}</Notice>}<form onSubmit={submit}><label>Email address<input name="email" type="email" autoComplete="email" placeholder="you@example.com" required /></label><label>Password<input name="password" type="password" autoComplete={signup ? "new-password" : "current-password"} minLength={signup ? 8 : 1} maxLength={72} required /></label>
        {signup && <p className="small muted">At least 8 characters; up to 72 UTF-8 bytes.</p>}<button type="submit" className="button primary full" disabled={busy}><ButtonLabel>{busy ? "Please wait…" : signup ? "Create account" : "Sign in"}</ButtonLabel></button></form>
      <p className="auth-switch">{signup ? "Already have an account?" : "New here?"} <Link href={signup ? "/login" : "/signup"}>{signup ? "Sign in" : "Create an account"}</Link></p></section></main>;
}
