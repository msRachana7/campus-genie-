// CAMPUS_GENIE_SIMPLE_LOGIN - email and password, no verification links.
import { useState, type FormEvent } from "react";
import { Sparkles } from "lucide-react";
import { authFetch, saveSession, type CampusUser } from "../lib/campusAuth";

export default function CampusLogin({ onLogin }: { onLogin: () => void }) {
  const [create, setCreate] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const form = new FormData(event.currentTarget);
    const value = (key: string) => String(form.get(key) ?? "");
    const body = create ? {
      email: email.trim().toLowerCase(), password: value("password"),
      name: value("name").trim(), usn: value("usn").trim(),
      department: value("department").trim(), year_of_study: Number(value("year_of_study")),
      contact_number: value("contact_number").trim() || null,
    } : { email: email.trim().toLowerCase(), password: value("password") };
    setBusy(true);
    setError("");
    try {
      const result = await authFetch<{ access_token: string; user: CampusUser }>(
        create ? "/api/auth/register" : "/api/auth/login",
        { method: "POST", body: JSON.stringify(body) },
      );
      if (!result.access_token || !result.user) throw new Error("The backend returned no login token. Check that both backend replacement files were copied.");
      saveSession(result.access_token, result.user);
      onLogin();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in. Please try again.");
    } finally { setBusy(false); }
  }

  return (
    <main className="login-screen" style={{ minHeight: "100dvh", height: "auto", padding: "32px 16px", overflowY: "auto", alignItems: "flex-start" }}>
      <section className="login-card" style={{ width: "100%", maxWidth: 500, margin: "24px auto", boxSizing: "border-box" }}>
        <div className="login-brand"><div className="brand-mark"><Sparkles size={20} /></div><div><b>campus genie</b><span>Your campus, made findable</span></div></div>
        <div className="login-copy">
          <h1 style={{ fontSize: 36 }}>{create ? "Create your account" : "Welcome back"}</h1>
          <p>{create ? "Register once and go straight into Campus Genie. No verification email." : "Sign in with your college email and Campus Genie password."}</p>
        </div>
        {error && <p className="login-error" role="alert">{error}</p>}
        <form key={String(create)} className="login-form" onSubmit={submit}>
          {create && <>
            <label>Full name<div className="login-input"><input name="name" required maxLength={120} autoComplete="name" /></div></label>
            <label>USN<div className="login-input"><input name="usn" required minLength={5} maxLength={24} /></div></label>
            <label>Department<div className="login-input"><input name="department" required maxLength={120} /></div></label>
            <label>Year<div className="login-input"><select name="year_of_study" required defaultValue="1">
              {[1, 2, 3, 4].map(year => <option key={year} value={year}>Year {year}</option>)}
            </select></div></label>
            <label>Contact number (optional)<div className="login-input"><input name="contact_number" type="tel" autoComplete="tel" maxLength={32} /></div></label>
          </>}
          <label>College email<div className="login-input"><input name="email" type="email" required autoComplete="email" maxLength={254}
            value={email} onChange={event => setEmail(event.target.value)} placeholder="you@bmsce.ac.in" /></div></label>
          <label>Password<div className="login-input"><input name="password" type="password" required minLength={create ? 12 : 1} maxLength={256}
            autoComplete={create ? "new-password" : "current-password"} /></div>{create && <small>At least 12 characters. Use a separate password for this app.</small>}</label>
          <button className="login-submit" type="submit" disabled={busy}>{busy ? "Please wait..." : create ? "Create account and enter" : "Sign in"}</button>
        </form>
        <div className="login-links" style={{ marginTop: 20 }}>
          <button type="button" disabled={busy} onClick={() => { setCreate(!create); setError(""); }}>
            {create ? "Already registered? Sign in" : "New here? Create an account"}
          </button>
        </div>
      </section>
    </main>
  );
}
