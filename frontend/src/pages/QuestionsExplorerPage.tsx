import { useEffect,useState } from "react";
import { Link,useNavigate } from "react-router-dom";
import { AppChrome } from "../app/layout/AppChrome";
import { Card } from "../components/common/Card";
import { EmptyState } from "../components/common/EmptyState";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { PageTitle } from "../components/layout/PageTitle";
import { listQuestions } from "../app/services/questions";
import { useKnowledgeBase } from "../app/hooks/useKnowledgeBase";
export default function QuestionsExplorerPage(){
 const {knowledgeBaseId}=useKnowledgeBase();const [items,setItems]=useState<any[]>([]),[total,setTotal]=useState(0),[q,setQ]=useState(""),[type,setType]=useState("");const [loading,setLoading]=useState(true);const [error,setError]=useState("");const nav=useNavigate();
 useEffect(()=>{if(!knowledgeBaseId)return;setLoading(true);listQuestions(knowledgeBaseId,{q:q||undefined,question_type:type||undefined,limit:100}).then(x=>{setItems(x.items);setTotal(x.total)}).catch(e=>setError(e instanceof Error?e.message:"Unable to load questions")).finally(()=>setLoading(false))},[knowledgeBaseId,q,type]);
 return <AppChrome title="Questions Explorer"><PageTitle title="Question bank" subtitle={total+" canonical question(s)"} action={<Link className="btn primary" to="/practice">Practice</Link>}/><div className="filters"><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search question text…"/><select value={type} onChange={e=>setType(e.target.value)}><option value="">All types</option><option value="mcq">MCQ</option><option value="short_answer">Short answer</option><option value="numerical">Numerical</option></select></div>{error&&<Card><p className="upload-error">{error}</p></Card>}{loading?<LoadingSpinner label="Loading question bank…"/>:!items.length?<EmptyState title="No questions" description="Generate or ingest questions into this knowledge base first."/>:<div className="stack">{items.map((x:any)=><Card key={x.id}><div className="result-meta"><span className="tag purple">{x.question_type}</span><span>{x.difficulty==null?"Unrated":"Difficulty "+x.difficulty}</span></div><h3>{x.text}</h3><p>{[x.classification?.subject,x.classification?.topic,x.classification?.subtopic].filter(Boolean).join(" · ")||"No classification"}</p><button className="btn" onClick={()=>nav("/question?id="+encodeURIComponent(x.id))}>Open question</button></Card>)}</div>}</AppChrome>;
}