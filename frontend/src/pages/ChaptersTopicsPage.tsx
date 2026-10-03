import {useEffect,useState} from "react";
import {AppChrome} from "../app/layout/AppChrome";
import {Card} from "../components/common/Card";
import {EmptyState} from "../components/common/EmptyState";
import {LoadingSpinner} from "../components/common/LoadingSpinner";
import {PageTitle} from "../components/layout/PageTitle";
import {getHierarchy} from "../app/services/workspace";
import {useKnowledgeBase} from "../app/hooks/useKnowledgeBase";
export default function ChaptersTopicsPage(){
 const {knowledgeBaseId}=useKnowledgeBase();const [data,setData]=useState<any>();
 useEffect(()=>{if(knowledgeBaseId)getHierarchy(knowledgeBaseId).then(setData).catch(()=>{})},[knowledgeBaseId]);
 return <AppChrome title="Chapters & Topics"><PageTitle title="Chapters and topics" subtitle="Live hierarchy extracted from document versions."/>
 {!data?<LoadingSpinner label="Loading hierarchy…"/>:!data.sections?.length?<EmptyState title="No structure yet" description="Process a document to discover chapters and topics."/>:<div className="stack">{data.sections.map((s:any)=><Card key={s.id}><h3>{s.title}</h3>{s.chapters.map((c:any)=><div className="chapter" key={c.id}><b>CH</b><span><strong>{c.title}</strong><small>{c.topics?.length||0} topics · {c.topics?.reduce((n:number,t:any)=>n+(t.subtopics?.length||0),0)} subtopics</small></span></div>)}</Card>)}</div>}
 </AppChrome>;
}