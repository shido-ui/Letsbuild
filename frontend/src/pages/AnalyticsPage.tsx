import {useEffect,useState} from "react";
import {AppChrome} from "../app/layout/AppChrome";
import {Card} from "../components/common/Card";
import {LoadingSpinner} from "../components/common/LoadingSpinner";
import {PageTitle} from "../components/layout/PageTitle";
import {useKnowledgeBase} from "../app/hooks/useKnowledgeBase";
import {getAnalytics} from "../app/services/analytics";
import {MasteryChart} from "../components/analytics/MasteryChart";
import {TrendChart} from "../components/analytics/TrendChart";
import {WeaknessHeatmap} from "../components/analytics/WeaknessHeatmap";
export default function AnalyticsPage(){
 const {knowledgeBaseId}=useKnowledgeBase();const [days,setDays]=useState(30);const [data,setData]=useState<any>();
 useEffect(()=>{if(knowledgeBaseId)getAnalytics(knowledgeBaseId,days).then(setData).catch(()=>{})},[knowledgeBaseId,days]);
 const mastery=data?.mastery||data?.topics||[];const trend=data?.trend||data?.daily_accuracy||[];
 return <AppChrome title="Analytics"><PageTitle title="Learning analytics" subtitle="Derived from persisted practice and learning events." action={<select value={days} onChange={e=>setDays(Number(e.target.value))}><option value={7}>7 days</option><option value={30}>30 days</option><option value={90}>90 days</option></select>}/>{!data?<LoadingSpinner label="Loading analytics…"/>:<><div className="grid3"><Card><b className="big-stat">{data.total_events||0}</b><small>Events</small></Card><Card><b className="big-stat">{data.practice_sessions||0}</b><small>Practice sessions</small></Card><Card><b className="big-stat">{data.accuracy==null?"—":Math.round(data.accuracy)+"%"}</b><small>Accuracy</small></Card></div><Card><h3>Mastery</h3><MasteryChart data={mastery}/></Card><Card><h3>Accuracy trend</h3><TrendChart data={trend}/></Card><Card><h3>Weakness map</h3><WeaknessHeatmap items={mastery}/></Card></>}</AppChrome>;
}