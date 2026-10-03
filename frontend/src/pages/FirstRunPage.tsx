import {useNavigate} from "react-router-dom";
import {AppChrome} from "../app/layout/AppChrome";
import {Card} from "../components/common/Card";
import {PageTitle} from "../components/layout/PageTitle";
import {useKnowledgeBase} from "../app/hooks/useKnowledgeBase";
import {createKnowledgeBase} from "../app/services/workspace";
export default function FirstRunPage(){
 const {items}=useKnowledgeBase();const nav=useNavigate();
 const setup=async()=>{await createKnowledgeBase("My Knowledge");nav("/upload")};
 return <AppChrome title="First Run"><PageTitle title="Welcome to ModuleIQ" subtitle="Set up the local knowledge workspace before adding your first source."/><Card><div className="first"><div className="orb">M</div><h1>From source material to structured knowledge.</h1><p>ModuleIQ keeps documents, extracted structure, questions, solutions and learning records tied together.</p>{items.length?<button className="btn primary" onClick={()=>nav("/dashboard")}>Open workspace</button>:<button className="btn primary" onClick={()=>void setup()}>Create knowledge workspace</button>}<div className="steps"><span>01 · Workspace</span><span>02 · Material</span><span>03 · Structure</span><span>04 · Practice</span></div></div></Card></AppChrome>;
}