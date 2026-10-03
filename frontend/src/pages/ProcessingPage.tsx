import { useEffect,useState } from "react";
import { useSearchParams,Link } from "react-router-dom";
import { AppChrome } from "../app/layout/AppChrome";
import { Card } from "../components/common/Card";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ProcessingStatus } from "../components/upload/ProcessingStatus";
import { getProcessingJob } from "../app/services/ingestion";
export default function ProcessingPage(){
 const [params]=useSearchParams();const id=params.get("job");const [job,setJob]=useState<any>();const [error,setError]=useState("");
 useEffect(()=>{if(!id)return;let active=true;let timer:number;const poll=async()=>{try{const value=await getProcessingJob(id);if(!active)return;setJob(value);if(!["complete","completed","failed"].includes(value.status))timer=window.setTimeout(poll,1200);}catch(e){if(active)setError(e instanceof Error?e.message:"Unable to read processing job")}};void poll();return()=>{active=false;window.clearTimeout(timer)}},[id]);
 return <AppChrome title="AI Processing"><div className="title"><div><h2>Material processing</h2><p>{id?"Tracking persisted job "+id:"No processing job selected."}</p></div></div>{!id&&<Card><p>Upload a material first, then return here to monitor extraction.</p><Link className="btn primary" to="/upload">Upload</Link></Card>}{error&&<Card><p className="upload-error">{error}</p></Card>}{id&&!job&&<LoadingSpinner label="Loading processing state…"/>}{job&&<><Card><div className="result-meta"><b>Status: {job.status}</b><span>Attempt {job.attempts}</span></div><p>{job.error||"The worker reports stage progress from the canonical processing job."}</p></Card><Card><ProcessingStatus stages={job.stages}/></Card>{["complete","completed"].includes(job.status)&&<Link className="btn primary" to={"/document?version="+encodeURIComponent(job.document_version_id)}>Open document version</Link>}</>}</AppChrome>;
}