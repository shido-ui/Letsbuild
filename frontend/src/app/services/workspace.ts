import { apiClient } from "../api/client";

export type KnowledgeBase={id:string;workspace_id:string;name:string;description?:string|null};
export type WorkspaceOverview=KnowledgeBase & {counts:Record<string,number>;materials:Array<{id:string;name:string;media_type:string;size_bytes?:number|null;sha256?:string|null;metadata?:Record<string,unknown>;documents:Array<{id:string;title?:string|null;current_version_id?:string|null}>}>};
export async function listKnowledgeBases(){const {data}=await apiClient.get<KnowledgeBase[]>("/ingestion/knowledge-bases");return data;}
export async function createKnowledgeBase(name:string){const {data}=await apiClient.post<KnowledgeBase>("/ingestion/knowledge-bases",null,{params:{name}});return data;}
export async function getWorkspace(id:string){const {data}=await apiClient.get<WorkspaceOverview>("/knowledge-bases/"+id);return data;}
export async function getHierarchy(id:string){const {data}=await apiClient.get("/knowledge-bases/"+id+"/hierarchy");return data;}
export async function getSource(kind:string,id:string){const {data}=await apiClient.get("/knowledge-bases/source/"+kind+"/"+id);return data;}