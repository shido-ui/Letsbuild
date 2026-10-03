import { Link } from "react-router-dom";
import { AppChrome } from "../app/layout/AppChrome";
import { useKnowledgeBase } from "../app/hooks/useKnowledgeBase";

export function DashboardPage() {
  const { knowledgeBase, loading, error } = useKnowledgeBase();
  if (loading) return <AppChrome title="Dashboard"><div className="card"><h2>Loading workspace…</h2></div></AppChrome>;
  if (error) return <AppChrome title="Dashboard"><div className="card"><h2>Workspace needs material</h2><p>{error}</p><Link className="btn primary" to="/upload">Add material</Link></div></AppChrome>;
  const c = knowledgeBase.counts || {};
  return <AppChrome title="Dashboard"><div className="title"><div><span className="tag purple">KNOWLEDGE WORKSPACE</span><h1>Turn material into knowledge.</h1><p>{knowledgeBase.description || "Your local-first learning workspace."}</p></div><Link className="btn primary" to="/upload">＋ Add material</Link></div>
    <div className="grid3">
      {[[c.documents,"Documents","/library"],[c.questions,"Questions","/questions"],[c.topics,"Topics","/chapters"],[c.solutions,"Solutions","/questions"],[c.pages,"Pages","/library"],[c.equations,"Equations","/library"]].map(([n,label,to])=><Link className="card" to={to as string} key={label}><span className="tag">{label}</span><h2>{n || 0}</h2><p>Open {label.toLowerCase()}</p></Link>)}
    </div>
    <section className="card"><h2>Recent material</h2>{knowledgeBase.materials?.length ? knowledgeBase.materials.slice(0,6).map((m:any)=><div className="provider" key={m.id}><span><strong>{m.name}</strong><small>{m.media_type || "document"} · {m.documents?.length || 0} document(s)</small></span><Link className="btn" to={`/document/${m.documents?.[0]?.id || m.id}`}>Open</Link></div>) : <p>No material yet.</p>}</section>
  </AppChrome>;
}
