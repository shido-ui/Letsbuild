import {apiClient} from "../api/client";
export type QuestionOption={id:string;ordinal:number;text:string};
export type Question={id:string;text:string;question_type:string;difficulty:number|null;classification?:{subject?:string|null;topic?:string|null;subtopic?:string|null}|null;options:QuestionOption[];metadata?:Record<string,unknown>};
export async function listQuestions(kbId:string,params:{q?:string;question_type?:string;limit?:number;offset?:number}={}){const {data}=await apiClient.get<{items:Question[];total:number;limit:number;offset:number}>("/questions",{params:{knowledge_base_id:kbId,...params}});return data;}
export async function getQuestion(id:string){const {data}=await apiClient.get<Question>("/questions/"+id);return data;}