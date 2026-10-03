import {useState} from "react";
import {AppChrome} from "../app/layout/AppChrome";
import {Card} from "../components/common/Card";
import {PageTitle} from "../components/layout/PageTitle";
import {SearchResults} from "../components/search/SearchResults";
import {SearchFilters} from "../components/search/SearchFilters";
import {searchKnowledge} from "../app/services/search";
import {useKnowledgeBase} from "../app/hooks/useKnowledgeBase";
export default function SearchPage(){
 const {knowledgeBaseId}=useKnowledgeBase();const [q,setQ]=useState("");const [kind,setKind]=useState("");const [data,setData]=useState<any>();const [busy,setBusy]=useState(false);
 const run=async()=>{if(!knowledgeBaseId||!q.trim())return;setBusy(true);try{setData(await searchKnowledge(knowledgeBaseId,q,{kind:kind||undefined}))}catch{}finally{setBusy(false)}};
 return <AppChrome title="Search"><PageTitle title="Search knowledge" subtitle="Full-text search across canonical documents, structure, questions and solutions."/><Card className="searchcard"><input autoFocus value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>{if(e.key==="Enter")void run()}} placeholder="Search concepts, questions, equations…"/><div className="filters"><SearchFilters kind={kind} onKind={setKind}/><button className="btn primary" disabled={busy||!q.trim()} onClick={()=>void run()}>{busy?"Searching…":"Search"}</button></div></Card>{data&&<><Card><div className="result-meta"><b>{data.results?.length||0} matches</b><span>{data.related_concepts?.length||0} related concepts</span></div></Card><SearchResults results={data.results||[]}/></>}</AppChrome>;
}