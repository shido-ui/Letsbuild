import { useState } from "react";
import { useDropzone } from "react-dropzone";
import { useNavigate } from "react-router-dom";
import { AppChrome } from "../app/layout/AppChrome";
import { apiClient, getRuntimeMode } from "../app/api/client";
import { addLocalMaterial } from "../app/api/localDb";
import { processLocalDocument } from "../app/api/localDocumentEngine";
import { buildLocalChunks } from "../app/api/localChunks";
import { buildLocalStructure } from "../app/api/localStructure";
import { useKnowledgeBase } from "../app/hooks/useKnowledgeBase";

export function UploadPage() {
 const {id,refresh}=useKnowledgeBase(); const nav=useNavigate(); const [busy,setBusy]=useState(false); const [status,setStatus]=useState("");
 const onDrop=async(files:File[])=>{if(!files.length||!id)return;setBusy(true);setStatus("");
 try{if(getRuntimeMode()==="standalone"){let ready=0;let failed=0;for(const file of files){const before=await addLocalMaterial(file,id);const material=before.materials.find((item)=>item.name===file.name&&item.size_bytes===file.size);if(!material)continue;const doc=material.documents[0];if(!doc)continue;const result=await processLocalDocument(material.id,doc.id);if(result.status==="ready"){await buildLocalChunks(result.id);await buildLocalStructure(result.id);ready+=1}else failed+=1;}setStatus(failed?`${ready} material(s) extracted locally; ${failed} failed.`:`${ready} material(s) extracted locally and are ready for search.`);await refresh();return;}
 for(const file of files){const body=new FormData();body.append("file",file);body.append("knowledge_base_id",id);const r=await apiClient.post("/ingestion/upload",body,{headers:{"Content-Type":"multipart/form-data"}});nav("/processing/"+r.data.processing_job_id);}}
 catch(e:any){setStatus(e.response?.data?.detail||e.message||"Upload failed.")}finally{setBusy(false);void refresh()}};
 const dz=useDropzone({onDrop,disabled:busy,accept:{"application/pdf":[".pdf"],"application/vnd.openxmlformats-officedocument.wordprocessingml.document":[".docx"]},maxSize:100*1024*1024});
 const standalone=getRuntimeMode()==="standalone";
 return <AppChrome title="Upload & Analyze"><div className="title"><div><h1>Add material</h1><p>{standalone?"Add private material directly to this device.":"Drop PDFs or DOCX files and ModuleIQ will turn them into structured knowledge."}</p></div></div><div {...dz.getRootProps()} className={"card dropzone "+(dz.isDragActive?"active":"")}><input {...dz.getInputProps()}/><h2>{busy?"Processing locally…":"Drop files here"}</h2><p>or click to choose files · PDF/DOCX · max 100 MB</p><button className="btn primary" type="button">Choose files</button></div>{status&&<div className="card upload-error">{status}</div>}<section className="grid3"><div className="card"><h3>{standalone?"Private storage":"OCR"}</h3><p>{standalone?"Files stay in the app's local vault and text extraction runs on-device.":"Scanned pages are processed through the document pipeline."}</p></div><div className="card"><h3>Structure</h3><p>Page boundaries and extracted text remain linked to the source material.</p></div><div className="card"><h3>{standalone?"Local extraction":"Questions"}</h3><p>{standalone?"PDF text and DOCX text are extracted without sending the source file to ModuleIQ.":"Extracted questions remain linked to their source material."}</p></div></section></AppChrome>;
}