import { useEffect } from "react";
export function usePolling(task:()=>Promise<void>,enabled:boolean,interval=1200){
 useEffect(()=>{if(!enabled)return;let active=true;const run=async()=>{if(!active)return;await task();if(active)timer=window.setTimeout(run,interval)};let timer=window.setTimeout(run,0);return()=>{active=false;window.clearTimeout(timer)}},[task,enabled,interval]);
}