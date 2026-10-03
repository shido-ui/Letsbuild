import { useState } from "react";
export function QuestionCard({question,onSubmit,disabled=false}:{question:any;onSubmit:(answer:string,elapsed:number)=>void;disabled?:boolean}){
 const [selected,setSelected]=useState(""),started=Date.now();
 const options=question?.options||[];
 return <div className="question-card"><div className="result-meta"><span className="tag purple">{question?.question_type||"QUESTION"}</span><span>{question?.difficulty!=null?"Difficulty "+question.difficulty:"Difficulty unrated"}</span></div><h1>{question?.text}</h1><div className="options">{options.map((o:any,i:number)=><button disabled={disabled} key={o.id} onClick={()=>setSelected(o.id)} className={selected===o.id?"option selected":"option"}><b>{String.fromCharCode(65+i)}</b>{o.text}</button>)}</div><button disabled={disabled||!selected} className="ui-button ui-button-primary" onClick={()=>onSubmit(selected,Date.now()-started)}>Submit answer</button></div>;
}