import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AppChrome } from "../app/layout/AppChrome";
import { PageTitle } from "../components/layout/PageTitle";
import { Card } from "../components/common/Card";
import { FileDropzone } from "../components/upload/FileDropzone";
import { UploadProgress } from "../components/upload/UploadProgress";
import { useKnowledgeBase } from "../app/hooks/useKnowledgeBase";
import { uploadMaterial } from "../app/services/ingestion";
export default function UploadPage(){
 const {knowledgeBaseId}=useKnowledgeBase(); const nav=useNavigate(); const [items,setItems]=useState<any[]>([]); const [busy,setBusy]=useState(false);
 const onFiles=async(files:File[])=>{if(!knowledgeBaseId)return;setBusy(true);setItems([]);for(const file of files){const row={file:file.name,percent:0,status:"Uploading…"};setItems(v=>[...v,row]);try{const result=await uploadMaterial(file,knowledgeBaseId,p=>setItems(v=>v.map(x=>x.file===file.name?{...x,percent:p}:x)));setItems(v=>v.map(x=>x.file===file.name?{...x,percent:100,status:"Queued"}:x));if(result.processing_job_id){nav("/processing?job="+encodeURIComponent(result.processing_job_id));return;}}catch(e){setItems(v=>v.map(x=>x.file===file.name?{...x,status:e instanceof Error?e.message:"Upload failed"}:x));}}setBusy(false)};
 return <AppChrome title="Upload & Analyze"><PageTitle title="Add material" subtitle="Upload canonical source material for extraction and analysis."/>
 <FileDropzone onFiles={onFiles} disabled={busy}/>{!knowledgeBaseId&&<Card><p>Create or select a knowledge base before uploading.</p></Card>}<div className="stack">{items.map(x=><UploadProgress key={x.file} file={x.file} percent={x.percent} status={x.status}/>)}</div>
 <Card><h3>Upload contract</h3><p>PDF content is copied into managed storage, hashed, validated and represented as a document version before asynchronous processing begins.</p><div className="grid3"><div><b>250 MB</b><small>maximum upload</small></div><div><b>10,000</b><small>maximum PDF pages</small></div><div><b>SHA-256</b><small>duplicate detection</small></div></div></Card></AppChrome>;
}