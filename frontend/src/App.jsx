import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api";

const priorityLabels = { P0: "Critical", P1: "High", P2: "Normal", P3: "Low" };
function Badge({ children, tone = "neutral" }) { return <span className={`badge badge-${tone}`}>{children}</span>; }
function Priority({ value }) { return <Badge tone={value === "P0" ? "red" : value === "P1" ? "orange" : value === "P2" ? "blue" : "neutral"}>{value} · {priorityLabels[value] || "Unknown"}</Badge>; }

function CustomerPortal() {
  const [form, setForm] = useState({ customer_name: "", customer_email: "", message_text: "" });
  const [result, setResult] = useState(null); const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  function change(event) { setForm((current) => ({ ...current, [event.target.name]: event.target.value })); }
  async function submit(event) {
    event.preventDefault(); setLoading(true); setError(""); setResult(null);
    try { const data = await api.submitMessage(form); setResult(data); setForm((current) => ({ ...current, message_text: "" })); }
    catch (err) { setError(err.message || "Unable to submit your message. Please try again."); }
    finally { setLoading(false); }
  }
  return <div className="customer-layout">
    <section className="customer-intro"><span className="eyebrow">FRONTLINE CUSTOMER CARE</span><h1>How can we<br/><em>help you today?</em></h1><p>Send your message to our support team. Frontline will organise your request and route it to the right people.</p><div className="trust-note"><span className="trust-dot"/> Your request is saved for the support team.</div></section>
    <section className="panel form-panel"><div className="panel-heading"><div><span className="eyebrow">NEW SUPPORT REQUEST</span><h2>Send a message</h2></div><span className="step-number">01 / 01</span></div>
      <form onSubmit={submit} className="form-grid">
        <label>Your name<input name="customer_name" value={form.customer_name} onChange={change} placeholder="e.g. Alex Morgan" maxLength="120" required/></label>
        <label>Email address<input name="customer_email" type="email" value={form.customer_email} onChange={change} placeholder="alex@example.com" maxLength="254" required/></label>
        <label className="full-width">How can we help?<textarea name="message_text" value={form.message_text} onChange={change} placeholder="Describe your question or issue..." rows="6" maxLength="20000" required/></label>
        <div className="form-footer full-width"><span>Be as detailed as you can.</span><button className="button button-primary" disabled={loading}>{loading ? "Submitting…" : "Submit message"} <span>↗</span></button></div>
      </form>
      {error && <div className="alert alert-error">{error}</div>}
      {result && <div className="result-card"><div className="result-top"><Badge tone="green">Message received</Badge><span className="muted">Ticket #{result.id}</span></div><h3>Thank you. Your message has been received.</h3><p>Our support team has received your request. Please keep your ticket number for future reference.</p></div>}
    </section>
  </div>;
}

function SupportLogin({ onLogin }) {
  const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  async function submit(event) {
    event.preventDefault(); setLoading(true); setError("");
    try {
      const session = await api.login({ email, password });
      sessionStorage.setItem("frontline_access_token", session.access_token);
      onLogin(session.staff);
    } catch (err) { setError(err.message || "Unable to sign in."); }
    finally { setLoading(false); }
  }
  return <div className="login-wrap"><section className="panel login-panel"><span className="eyebrow">STAFF SIGN IN</span><h1>Welcome back</h1><p>Sign in with your individual support-agent account to access customer messages.</p><form onSubmit={submit}><label>Work email<input type="email" value={email} onChange={(e)=>setEmail(e.target.value)} placeholder="you@company.com" autoComplete="username" required/></label><label>Password<input type="password" value={password} onChange={(e)=>setPassword(e.target.value)} placeholder="Your password" autoComplete="current-password" required/></label><button className="button button-primary" disabled={loading}>{loading ? "Signing in…" : "Sign in to support"}</button></form>{error && <div className="alert alert-error">{error}</div>}</section></div>;
}
export default function App() {
  const [view,setView]=useState("customer");
  const [authenticated,setAuthenticated]=useState(()=>Boolean(sessionStorage.getItem("frontline_access_token")));
  const [authChecked,setAuthChecked]=useState(false);
  useEffect(()=>{
    const token=sessionStorage.getItem("frontline_access_token");
    if(!token){setAuthenticated(false);setAuthChecked(true);return;}
    api.me().then(()=>setAuthenticated(true)).catch(()=>{sessionStorage.removeItem("frontline_access_token");setAuthenticated(false);}).finally(()=>setAuthChecked(true));
  },[]);
  function logout(){sessionStorage.removeItem("frontline_access_token");setAuthenticated(false);setView("customer");}
  return <div className="app-shell"><header className="topbar"><a className="brand" href="#" onClick={(e)=>{e.preventDefault();setView("customer");}}><span className="brand-mark">F</span><span>frontline<small>SUPPORT INTELLIGENCE</small></span></a><nav><button className={view==="customer"?"nav-link active":"nav-link"} onClick={()=>setView("customer")}>Customer support</button><button className={view==="dashboard"?"nav-link active":"nav-link"} onClick={()=>setView("dashboard")}>Staff workspace</button></nav><div className="system-status"><span/> API workspace</div></header><main>{view==="customer"?<CustomerPortal/>:!authChecked?<div className="empty-state">Checking staff session…</div>:authenticated?<SupportDashboard onLogout={logout}/>:<SupportLogin onLogin={()=>setAuthenticated(true)}/>}</main><footer className="app-footer"><span>FRONTLINE AI TRIAGE</span><span>Structured decisions. Clear priorities. Better support.</span></footer></div>;
}
