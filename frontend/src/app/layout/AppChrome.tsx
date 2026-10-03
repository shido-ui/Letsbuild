import { NavLink, useLocation } from "react-router-dom";
import { useState, type ReactNode } from "react";
import { Menu, Search, Settings, HelpCircle, LogOut, X } from "lucide-react";
import { useAppStore } from "../store/useAppStore";

const items=[
  ["/dashboard","Dashboard"],["/upload","Upload & Analyze"],["/processing","AI Processing"],
  ["/library","Library"],["/document","Document Detail"],["/questions","Questions Explorer"],
  ["/review","Review Center"],["/chapters","Chapters & Topics"],["/practice","Practice"],
  ["/analytics","Analytics"],["/search","Search"]
] as const;

export function AppChrome({title,children}:{title:string;children:ReactNode}){
 const location=useLocation(),[open,setOpen]=useState(false),logout=useAppStore(s=>s.logout),user=useAppStore(s=>s.user);
 const close=()=>setOpen(false);
 const navigation=<aside className={open?"side mobile-open":"side"}>
   <div className="brand"><b>M</b><span><strong>ModuleIQ</strong><small>Knowledge workspace</small></span><button className="mobile-close" onClick={close} aria-label="Close navigation"><X size={17}/></button></div>
   <div className="workspace">● &nbsp;Personal workspace</div>
   <nav aria-label="Primary">
    {items.map(([to,label])=><NavLink key={to} to={to} onClick={close} className={({isActive})=>isActive?"nav active":"nav"}>{label}</NavLink>)}
   </nav>
   <div className="side-bottom">
    <NavLink to="/settings" onClick={close} className={({isActive})=>isActive?"nav active":"nav"}><Settings size={15}/> Settings</NavLink>
    <button className="nav" onClick={()=>{logout();close()}}><LogOut size={15}/> Sign out</button>
    <div className="profile"><b>{(user?.username||"U").slice(0,1).toUpperCase()}</b><span>{user?.username||"Local account"}<small>{user?.email||"Authenticated workspace"}</small></span></div>
   </div>
 </aside>;
 return <div className="app">{navigation}{open&&<button className="nav-scrim" onClick={close} aria-label="Close navigation overlay"/>}<div className="page"><header><button className="hamb" onClick={()=>setOpen(true)} aria-label="Open navigation"><Menu size={20}/></button><div><small>Workspace /</small><b>{title}</b></div><div className="top"><NavLink to="/search" className="search top-link"><Search size={15}/><span>Search knowledge...</span><kbd>⌘ K</kbd></NavLink><button aria-label="Help"><HelpCircle size={16}/></button></div></header><main>{children}</main></div></div>;
}
