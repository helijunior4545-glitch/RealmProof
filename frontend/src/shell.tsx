import {useEffect,useState} from "react";
import {createRoot} from "react-dom/client";
function ShellTools(){
 const [open,setOpen]=useState(false);
 const [query,setQuery]=useState("");
 const links=Array.from(document.querySelectorAll<HTMLAnchorElement>(".sidebar a.nav-link[href]")).map(a=>({href:a.href,label:a.textContent?.trim()||""}));
 useEffect(()=>{const key=(e:KeyboardEvent)=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){e.preventDefault();setOpen(v=>!v)}if(e.key==="Escape")setOpen(false)};window.addEventListener("keydown",key);return()=>window.removeEventListener("keydown",key)},[]);
 useEffect(()=>{if(!open)setQuery("")},[open]);
 return <><button type="button" className="rp-shell-trigger" aria-expanded={open} onClick={()=>setOpen(v=>!v)}>Navigate <kbd>Ctrl K</kbd></button>{open&&<div className="rp-shell-menu" role="region" aria-label="Workspace navigation"><label htmlFor="rp-shell-search">Find a workspace page</label><input id="rp-shell-search" autoFocus value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search navigation"/><nav>{links.filter(l=>l.label.toLowerCase().includes(query.toLowerCase())).map((l,i)=><a key={i} href={l.href}>{l.label}<span aria-hidden="true">↗</span></a>)}</nav><button type="button" onClick={()=>setOpen(false)}>Close</button></div>}</>;
}
const host=document.getElementById("rp-react-shell");if(host)createRoot(host).render(<ShellTools/>);
