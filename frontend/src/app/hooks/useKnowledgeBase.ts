import { useEffect, useState } from "react";
import { listKnowledgeBases } from "../services/workspace";
import { useAppStore } from "../store/useAppStore";
export function useKnowledgeBase(){
 const selected=useAppStore(s=>s.knowledgeBaseId),setSelected=useAppStore(s=>s.setKnowledgeBaseId);
 const [items,setItems]=useState<any[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState("");
 useEffect(()=>{let alive=true;(async()=>{try{const data=await listKnowledgeBases();if(!alive)return;setItems(data);if(!selected&&data[0])setSelected(data[0].id);}catch(e){if(alive)setError(e instanceof Error?e.message:"Unable to load knowledge bases");}finally{if(alive)setLoading(false);}})();return()=>{alive=false};},[selected,setSelected]);
 const current=items.find(x=>x.id===selected)||items[0]||null;
 return {items,current,knowledgeBaseId:current?.id||null,loading,error};
}