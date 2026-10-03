import { useDropzone } from "react-dropzone";
import { UploadCloud } from "lucide-react";
export function FileDropzone({onFiles,disabled=false}:{onFiles:(files:File[])=>void;disabled?:boolean}){
 const {getRootProps,getInputProps,isDragActive}=useDropzone({onDrop:onFiles,disabled,accept:{"application/pdf":[".pdf"]},multiple:true,maxSize:250*1024*1024});
 return <div {...getRootProps()} className={"dropzone"+(isDragActive?" active":"")+(disabled?" uploading":"")}><input {...getInputProps()}/><UploadCloud size={36}/><h3>{isDragActive?"Release to upload":"Add your material"}</h3><p>PDF files up to 250 MB. Tap or drag files here.</p><small>Files stay in your configured ModuleIQ backend.</small></div>;
}