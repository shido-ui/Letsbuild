import { Link,useNavigate } from "react-router-dom";
import { AppChrome } from "../app/layout/AppChrome";
import { Card } from "../components/common/Card";
import { EmptyState } from "../components/common/EmptyState";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { PageTitle } from "../components/layout/PageTitle";
import { useKnowledgeBase } from "../app/hooks/useKnowledgeBase";
import { getWorkspace } from "../app/services/workspace";
import { useEffect,useState } from "react";
export default function LibraryPage(){
 const {knowledgeBaseId,loading}=useKnowledgeBase();const [data,setData]=useState<any>();const nav=useNavigate();
 useEffect(()=>{if(knowledgeBaseId)getWorkspace(knowledgeBaseId).then(setData).catch(()=>{})},[knowledgeBaseId]);
 if(loading)return <AppChrome title="Library"><LoadingSpinner/></AppChrome>;
 const mats=data?.materials||[];
 return <AppChrome title="Library"><PageTitle title="Your materials" subtitle="Every uploaded source and its document objects." action={<Link className="btn primary" to="/upload">＋ Add material</Link>}/>{!mats.length?<EmptyState title="No materials yet" description="Upload your first PDF to populate the canonical library." action={<Link className="btn primary" to="/upload">Upload PDF</Link>}/>:<div className="grid3">{mats.map((m:any)=><Card key={m.id} className="material-card" ><div className="cover"><span>MODULEIQ</span><b>{m.name.slice(0,24)}</b></div><span className="tag">{(m.media_type||"file").toUpperCase()}</span><h3>{m.name}</h3><p>{m.documents?.length||0} document object(s) · {m.size_bytes?Math.round(m.size_bytes/1024/1024)+" MB":"size unavailable"}</p><button className="btn" onClick={()=>m.documents?.[0]?nav("/document?document="+m.documents[0].id):nav("/document")}>Open source</button></Card>)}</div>}</AppChrome>;
}