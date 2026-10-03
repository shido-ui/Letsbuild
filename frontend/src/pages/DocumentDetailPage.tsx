import { useEffect,useState } from "react";
import { useSearchParams,Link } from "react-router-dom";
import { AppChrome } from "../app/layout/AppChrome";
import { Card } from "../components/common/Card";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { getSource } from "../app/services/workspace";
export default function DocumentDetailPage(){
 const [params]=useSearchParams();const documentId=params.get("document"),versionId=params.get("version");const [data,setData]=useState<any>();const [error,setError]=useState("");
 useEffect(()=>{const id=documentId||versionId;if(!id)return;const kind=documentId?"document":"version";getSource(kind,id).then(setData).catch(e=>setError(e instanceof Error?e.message:"Source unavailable"))},[documentId,versionId]);
 return <AppChrome title="Document Detail"><div className="title"><div><h2>{data?.title||"Document detail"}</h2><p>Canonical source object with provenance retained through processing.</p></div><Link className="btn" to="/library">Back to library</Link></div>{!data&&!error&&<LoadingSpinner label="Loading source object…"/>}{error&&<Card><p className="upload-error">{error}</p></Card>}{data&&<><Card className="doc"><div className="cover"><span>MODULEIQ</span><b>DOCUMENT</b></div><div><span className="tag green">SOURCE PRESERVED</span><h1>{data.title||"Untitled"}</h1><p>Object ID: {data.id}</p><p>{data.metadata?.page_count?data.metadata.page_count+" pages":"Page count not recorded in this object."}</p></div></Card><Card><h3>Processing metadata</h3><pre className="data-pre">{JSON.stringify(data.metadata||{},null,2)}</pre></Card></>}</AppChrome>;
}