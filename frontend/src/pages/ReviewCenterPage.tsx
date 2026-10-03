import {useEffect,useState} from "react";
import {AppChrome} from "../app/layout/AppChrome";
import {Card} from "../components/common/Card";
import {EmptyState} from "../components/common/EmptyState";
import {LoadingSpinner} from "../components/common/LoadingSpinner";
import {PageTitle} from "../components/layout/PageTitle";
import {listReviewItems,updateReviewItem} from "../app/services/review";
import {useKnowledgeBase} from "../app/hooks/useKnowledgeBase";

export default function ReviewCenterPage(){
 const {knowledgeBaseId}=useKnowledgeBase();const [items,setItems]=useState<any[]>([]);const [status,setStatus]=useState("open");const [loading,setLoading]=useState(true);
 useEffect(()=>{if(!knowledgeBaseId)return;setLoading(true);listReviewItems(knowledgeBaseId,status).then(setItems).catch(()=>setItems([])).finally(()=>setLoading(false))},[knowledgeBaseId,status]);
 const close=async(id:string)=>{try{await updateReviewItem(id,{status:"resolved"});setItems(v=>v.filter(x=>x.id!==id));}catch{}};
 return <AppChrome title="Review Center"><PageTitle title="Review center" subtitle="Items requiring human attention before knowledge is trusted."/>
 <div className="filters"><label>Status<select value={status} onChange={e=>setStatus(e.target.value)}><option value="open">Open</option><option value="resolved">Resolved</option></select></label></div>
 {loading?<LoadingSpinner/>:!items.length?<EmptyState title="Review queue is clear" description="No review items match the current filter."/>:<div className="stack">{items.map(x=><Card key={x.id}><div className="result-meta"><span className="tag purple">{x.entity_type}</span><span>{x.reason}</span></div><h3>{x.entity_id}</h3><p>{x.metadata_json?JSON.stringify(x.metadata_json):"No additional metadata."}</p>{x.status==="open"&&<button className="btn" onClick={()=>void close(x.id)}>Mark resolved</button>}</Card>)}</div>}
 </AppChrome>;
}