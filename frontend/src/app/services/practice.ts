import {apiClient} from "../api/client";
export type PracticeData={id:string;knowledge_base_id:string;mode:string;status:string;current_index:number;total_questions:number;current_question?:any;questions:any[];attempts:any[];config:Record<string,unknown>};
export async function createPractice(payload:{knowledge_base_id:string;mode:string;limit:number;topic_id?:string;difficulty?:string;question_type?:string}){const {data}=await apiClient.post<PracticeData>("/practice/sessions",payload);return data;}
export async function getPractice(id:string){const {data}=await apiClient.get<PracticeData>("/practice/sessions/"+id);return data;}
export async function submitAttempt(id:string,payload:{question_id:string;answer_text?:string|null;skipped?:boolean;time_ms?:number;confidence?:number}){const {data}=await apiClient.post<PracticeData>("/practice/sessions/"+id+"/attempt",payload);return data;}
export async function pausePractice(id:string){const {data}=await apiClient.post<PracticeData>("/practice/sessions/"+id+"/pause");return data;}
export async function resumePractice(id:string){const {data}=await apiClient.post<PracticeData>("/practice/sessions/"+id+"/resume");return data;}
export async function finishPractice(id:string){const {data}=await apiClient.post("/practice/sessions/"+id+"/finish");return data;}
export async function practiceResults(id:string){const {data}=await apiClient.get("/practice/sessions/"+id+"/results");return data;}