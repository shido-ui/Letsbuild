import {useEffect,useState} from "react";
import {useNavigate,useSearchParams} from "react-router-dom";
import {AppChrome} from "../app/layout/AppChrome";
import {Card} from "../components/common/Card";
import {LoadingSpinner} from "../components/common/LoadingSpinner";
import {QuestionCard} from "../components/practice/QuestionCard";
import {Timer} from "../components/practice/Timer";
import {getPractice,submitAttempt,pausePractice,resumePractice,finishPractice} from "../app/services/practice";
export default function PracticeSessionPage(){
 const [params]=useSearchParams();const id=params.get("id");const nav=useNavigate();const [session,setSession]=useState<any>();const [error,setError]=useState("");
 useEffect(()=>{if(id)getPractice(id).then(setSession).catch(e=>setError(e instanceof Error?e.message:"Session unavailable"))},[id]);
 if(!id)return <AppChrome title="Practice Session"><Card><p>Select a practice session first.</p></Card></AppChrome>;
 if(!session&&!error)return <AppChrome title="Practice Session"><LoadingSpinner/></AppChrome>;
 if(error)return <AppChrome title="Practice Session"><Card><p className="upload-error">{error}</p></Card></AppChrome>;
 const finished=session.status==="completed"||session.current_index>=session.total_questions;
 const submit=async(answer:string,elapsed:number)=>{try{const next=await submitAttempt(id,{question_id:session.current_question.id,answer_text:answer,time_ms:elapsed});setSession(next);if(next.status==="completed")nav("/practice/results?id="+encodeURIComponent(id));}catch(e){setError(e instanceof Error?e.message:"Answer could not be submitted")}};
 return <AppChrome title="Practice Session"><div className="sessionbar"><div><h2>{session.mode} session</h2><p>{session.current_index} / {session.total_questions}</p></div><Timer startedAt={session.started_at} paused={session.status==="paused"}/></div>{error&&<Card><p className="upload-error">{error}</p></Card>}{finished?<Card><h2>Session complete</h2><button className="btn primary" onClick={()=>nav("/practice/results?id="+encodeURIComponent(id))}>View results</button></Card>:session.current_question?<><QuestionCard question={session.current_question} onSubmit={submit} disabled={session.status!=="active"}/><div className="actions"><button className="btn" onClick={()=>{const p=session.status==="active"?pausePractice(id):resumePractice(id);p.then(setSession).catch(()=>setError("Could not change session state"))}}>{session.status==="active"?"Pause":"Resume"}</button><button className="btn" onClick={()=>void finishPractice(id).then(()=>nav("/practice/results?id="+encodeURIComponent(id)))}>Finish</button></div></>:<Card><p>No current question is available.</p></Card>}</AppChrome>;
}