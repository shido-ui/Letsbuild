import {useState} from "react";
import {useNavigate} from "react-router-dom";
import {AppChrome} from "../app/layout/AppChrome";
import {Card} from "../components/common/Card";
import {PageTitle} from "../components/layout/PageTitle";
import {createPractice} from "../app/services/practice";
import {useKnowledgeBase} from "../app/hooks/useKnowledgeBase";

const modes=[
  ["fast","Fast Mode","Rapid review using the canonical question bank."],
  ["deep","Deep Practice","Work deliberately through each question."],
  ["boss","Boss Session","Long-form practice across the available bank."],
  ["custom","Custom","Choose question count and difficulty."]
];

export default function PracticePage(){
  const {knowledgeBaseId}=useKnowledgeBase();
  const nav=useNavigate();
  const [limit,setLimit]=useState(10);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const start=async(mode:string)=>{
    if(!knowledgeBaseId)return;
    setBusy(true);setError("");
    try{
      const s=await createPractice({knowledge_base_id:knowledgeBaseId,mode,limit});
      nav("/practice/session?id="+encodeURIComponent(s.id));
    }catch(e){
      setError(e instanceof Error?e.message:"Unable to create practice session");
    }finally{setBusy(false)}
  };
  return <AppChrome title="Practice">
    <PageTitle title="Practice engine" subtitle="Sessions are persisted and can update adaptive learning state."/>
    <Card>
      <label className="inline-field">Question count
        <input type="number" min="1" max="100" value={limit} onChange={e=>setLimit(Number(e.target.value)||1)}/>
      </label>
      {error&&<p className="upload-error">{error}</p>}
    </Card>
    <div className="grid3">
      {modes.map(m=><Card key={m[0]}>
        <span className="tag purple">{m[0].toUpperCase()}</span>
        <h3>{m[1]}</h3><p>{m[2]}</p>
        <button className="btn primary" disabled={busy||!knowledgeBaseId} onClick={()=>void start(m[0])}>{busy?"Starting…":"Start session"}</button>
      </Card>)}
    </div>
  </AppChrome>;
}
