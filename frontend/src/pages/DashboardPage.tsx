import { Link } from "react-router-dom";
import { AppChrome } from "../app/layout/AppChrome";
import { Card } from "../components/common/Card";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { EmptyState } from "../components/common/EmptyState";
import { PageTitle } from "../components/layout/PageTitle";
import { useKnowledgeBase } from "../app/hooks/useKnowledgeBase";
import { useEffect,useState } from "react";
import { getWorkspace } from "../app/services/workspace";

export default function DashboardPage(){
 const {knowledgeBaseId,loading,error}=useKnowledgeBase(); const [data,setData]=useState<any>(null);
 useEffect(()=>{if(!knowledgeBaseId)return;let alive=true;getWorkspace(knowledgeBaseId).then(v=>alive&&setData(v)).catch(()=>{});return()=>{alive=false}},[knowledgeBaseId]);
 if(loading)return <AppChrome title="Dashboard"><LoadingSpinner label="Loading workspace…"/></AppChrome>;
 if(error)return <AppChrome title="Dashboard"><EmptyState title="Workspace unavailable" description={error}/></AppChrome>;
 const c=data?.counts||{};
 return <AppChrome title="Dashboard"><PageTitle title={data?.name||"Knowledge workspace"} subtitle="Your canonical learning workspace, backed by the ModuleIQ database." action={<Link className="btn primary" to="/upload">＋ Add material</Link>}/>
 <div className="hero"><Card className="hero-card"><span className="tag purple">KNOWLEDGE WORKSPACE</span><h1>Turn your material into <em>knowledge.</em></h1><p>Upload notes and question papers. ModuleIQ preserves sources, extracts structure and makes the result searchable and practice-ready.</p><Link className="btn primary" to="/upload">Bring material</Link></Card>
 <Card><span>Knowledge health</span><strong className="big-stat">{c.materials?Math.min(100,Math.round(((c.topics||0)+(c.questions||0)+(c.solutions||0))/(Math.max(1,c.materials*20+(c.questions||0)+(c.solutions||0)))*100)):0}%</strong><div className="bar"><i style={{width:(c.materials?Math.min(100,Math.round(((c.topics||0)+(c.questions||0)+(c.solutions||0))/(Math.max(1,c.materials*20+(c.questions||0)+(c.solutions||0)))*100)):0)+"%"}}/></div></Card></div>
 <div className="grid3">{[["Materials",c.materials||0,"/library"],["Documents",c.documents||0,"/library"],["Questions",c.questions||0,"/questions"]].map(x=><Link className="stat-link" to={x[2] as string} key={x[0]}><Card><span className="tag purple">{x[0]}</span><h2>{x[1]}</h2><p>Open live data</p></Card></Link>)}</div>
 <PageTitle title="Knowledge structure" subtitle="Counts come from canonical objects, not demo fixtures."/>
 <div className="grid3"><Card><h3>{c.chapters||0} chapters</h3><p>{c.topics||0} topics · {c.concepts||0} concepts</p><Link className="btn" to="/chapters">Browse hierarchy</Link></Card><Card><h3>{c.equations||0} equations</h3><p>{c.tables||0} tables · {c.diagrams||0} diagrams</p><Link className="btn" to="/search">Search objects</Link></Card><Card><h3>{c.solutions||0} solutions</h3><p>{c.verified_solutions||0} verified</p><Link className="btn" to="/review">Open review</Link></Card></div></AppChrome>;
}