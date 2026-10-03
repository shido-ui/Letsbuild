import { useState } from "react";
import { useDropzone } from "react-dropzone";
import { useNavigate } from "react-router-dom";
import { AppChrome } from "../app/layout/AppChrome";
import { apiClient } from "../app/api/client";
import { useKnowledgeBase } from "../app/hooks/useKnowledgeBase";

export function UploadPage() {
 const {id, refresh}=useKnowledgeBase(); const nav=useNavigate(); const [busy,setBusy]=useState(false); const [status,setStatus]=useState("");
 const onDrop=async(files:File[])=>{if(!files.length)return;setBusy(true);setStatus("");try{for(const file of files){const body=new FormData();body.append("file",file);if(id)body.append("knowledge_base_id",id);const r=await apiClient.post("/ingestion/upload",body,{headers:{"Content-Type":"multipart/form-data"}});nav(`/processing/${r.data.processing_job_id}`);}}catch(e:any){setStatus(e.response?.data?.detail||"Upload failed.")}finally{setBusy(false);void refresh()}};
 const dz=useDropzone({onDrop,disabled:busy,accept:{"application/pdf":[".pdf"],"application/vnd.openxmlformats-officedocument.wordprocessingml.document":[".docx"]},maxSize:100*1024*1024});
 return <AppChrome title="Upload & Analyze"><div className="title"><div><h1>Add material</h1><p>Drop PDFs or DOCX files and ModuleIQ will turn them into structured knowledge.</p></div></div><div {...dz.getRootProps()} className={`card dropzone ${dz.isDragActive?"active":""}`}><input {...dz.getInputProps()}/><h2>{busy?"Processing upload…":"Drop files here"}</h2><p>or click to choose files · PDF/DOCX · max 100 MB</p><button className="btn primary" type="button">Choose files</button></div>{status&&<div className="card upload-error">{status}</div>}<section className="grid3"><div className="card"><h3>OCR</h3><p>Scanned pages are processed through the document pipeline.</p></div><div className="card"><h3>Structure</h3><p>Chapters, topics, concepts and source links are preserved.</p></div><div className="card"><h3>Questions</h3><p>Extracted questions remain linked to their source material.</p></div></section></AppChrome>;
}
