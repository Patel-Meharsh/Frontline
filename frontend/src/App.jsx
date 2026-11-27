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
function Stat({ label, value }) { return <div className="panel stat-card"><span>{label}</span><strong>{value}</strong></div>; }

function SupportDashboard({ onLogout }) {
  const [messages,setMessages]=useState([]); const [stats,setStats]=useState(null); const [selected,setSelected]=useState(null);
  const [filter,setFilter]=useState("all"); const [search,setSearch]=useState(""); const [loading,setLoading]=useState(true);
  const [error,setError]=useState(""); const [saving,setSaving]=useState(false);
  const refresh=useCallback(async()=>{
    try {
      const params=filter==="all"?{limit:100}:{limit:100,status:filter};
      const [list,summary]=await Promise.all([api.getMessages(params),api.getStats()]);
      setMessages(list.items); setStats(summary);
      setSelected(current=>current?list.items.find(item=>item.id===current.id)||current:null);
      setError("");
    } catch(err) {
      setError(err.message||"Could not connect to Frontline API.");
    } finally { setLoading(false); }
  },[filter]);
  useEffect(()=>{refresh();},[refresh]);
  const visible=useMemo(()=>messages.filter(item=>{
    const needle=search.toLowerCase();
    return !needle||[item.customer_name,item.customer_email,item.message_text,item.decision?.category].some(v=>String(v||"").toLowerCase().includes(needle));
  }),[messages,search]);
  async function updateStatus(status){
    if(!selected)return;
    setSaving(true);
    try { const updated=await api.updateReview(selected.id,{status}); setSelected(updated); await refresh(); }
    catch(err){setError(err.message);}
    finally{setSaving(false);}
  }
  return <div className="dashboard-layout">
    <div className="dashboard-heading"><div><span className="eyebrow">SUPPORT OPERATIONS</span><h1>Message intelligence</h1><p>Every customer message, organised in one place.</p></div><div className="heading-actions"><button className="button button-secondary" onClick={refresh}>↻ Refresh</button><button className="button button-quiet" onClick={onLogout}>Sign out</button></div></div>
    <div className="stat-grid"><Stat label="Total messages" value={stats?.total_messages??"—"}/><Stat label="New requests" value={stats?.new_messages??"—"}/><Stat label="Needs human review" value={stats?.needs_human??"—"}/><Stat label="Resolved" value={stats?.resolved_messages??"—"}/></div>
    {error&&<div className="alert alert-error">{error}</div>}
    <div className="workspace"><section className="panel inbox-panel"><div className="inbox-toolbar"><div><span className="eyebrow">INCOMING</span><h2>All messages <span className="count">{visible.length}</span></h2></div><input className="search-input" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search messages…"/></div>
      <div className="filter-row">{[["all","All"],["new","New"],["in_review","In review"],["resolved","Resolved"]].map(([key,label])=><button key={key} className={filter===key?"filter active":"filter"} onClick={()=>setFilter(key)}>{label}</button>)}</div>
      <div className="message-list">{loading?<div className="empty-state">Loading messages…</div>:visible.length===0?<div className="empty-state">No messages found. New customer requests will appear here.</div>:visible.map(item=><button key={item.id} className={selected?.id===item.id?"message-row selected":"message-row"} onClick={()=>setSelected(item)}><div className="message-row-top"><strong>{item.customer_name}</strong><Priority value={item.decision?.priority}/></div><div className="message-email">{item.customer_email}</div><p>{item.decision?.summary||item.message_text}</p><div className="message-row-bottom"><span>{item.decision?.category?.replaceAll("_"," ")||"processing"}</span><span>{new Date(item.created_at).toLocaleString()}</span></div></button>)}</div>
    </section><section className="panel detail-panel">{!selected?<div className="empty-state detail-empty"><div className="empty-icon">↖</div><h3>Select a message</h3><p>Choose a request from the inbox to inspect its AI triage decision.</p></div>:<><div className="detail-header"><div><span className="eyebrow">TICKET #{selected.id}</span><h2>{selected.customer_name}</h2><span className="muted">{selected.customer_email}</span></div><Badge tone={selected.review_status==="resolved"?"green":selected.review_status==="in_review"?"blue":"orange"}>{selected.review_status.replace("_"," ")}</Badge></div>
      <div className="detail-section"><span className="eyebrow">ORIGINAL MESSAGE</span><p className="original-message">{selected.message_text}</p></div>
      {selected.decision&&<div className="detail-section"><div className="ai-title"><span className="ai-spark">✳</span><div><span className="eyebrow">FRONTLINE AI DECISION</span><h3>Recommended triage</h3></div></div><div className="decision-grid"><div><small>Category</small><strong>{selected.decision.category.replaceAll("_"," ")}</strong></div><div><small>Priority</small><Priority value={selected.decision.priority}/></div><div><small>Confidence signal</small><strong>{Math.round(selected.decision.confidence*100)}%</strong></div><div><small>Human review</small><strong>{selected.decision.needs_human?"Required":"Not flagged"}</strong></div></div><div className="decision-copy"><small>Summary</small><p>{selected.decision.summary}</p></div><div className="decision-copy"><small>Suggested action</small><p>{selected.decision.suggested_action}</p></div><div className="decision-foot">Model: {selected.decision.model_name} · {selected.decision.tokens_used} tokens · {selected.decision.latency_sec}s</div></div>}
      <div className="detail-actions"><span className="eyebrow">REVIEW STATUS</span><div className="action-buttons"><button disabled={saving} className="button button-secondary" onClick={()=>updateStatus("in_review")}>Mark in review</button><button disabled={saving} className="button button-primary" onClick={()=>updateStatus("resolved")}>{saving?"Saving…":"Resolve request"}</button></div></div></>}</section></div>
  </div>;
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
