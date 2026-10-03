import {useEffect,useState} from "react";
import {Link,useSearchParams} from "react-router-dom";
import {AppChrome} from "../app/layout/AppChrome";
import {Card} from "../components/common/Card";
import {LoadingSpinner} from "../components/common/LoadingSpinner";
import {ResultsSummary} from "../components/practice/ResultsSummary";
import {practiceResults} from "../app/services/practice";
export default function PracticeResultsPage(){const [params]=useSearchParams();const id=params.get("id");const [data,setData]=useState<any>();useEffect(()=>{if(id)practiceResults(id).then(setData).catch(()=>{})},[id]);return <AppChrome title="Practice Results"><div className="title"><div><h2>Session results</h2><p>Persisted results from your practice session.</p></div><Link className="btn" to="/practice">New session</Link></div>{!data?<LoadingSpinner label="Loading results…"/>:<><ResultsSummary data={data}/><Card><h3>Attempt review</h3>{data.attempts?.length?data.attempts.map((a:any,i:number)=><div className="weak" key={a.question_id}><span>Question {i+1}</span><b>{a.skipped?"Skipped":a.is_correct===true?"Correct":a.is_correct===false?"Incorrect":"Unscored"}</b></div>):<p>No attempts recorded.</p>}</Card></>}</AppChrome>}