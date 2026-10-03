import { NavLink, useLocation } from "react-router-dom";
import { useState } from "react";
import type { ReactNode } from "react";

const items = [
  ["/settings", "Settings", "⚙"],
  ["/dashboard", "Dashboard", "▦"],
  ["/upload", "Upload & Analyze", "↑"],
  ["/processing", "AI Processing", "✦"],
  ["/library", "Library", "▤"],
  ["/document", "Document Detail", "▱"],
  ["/questions", "Questions Explorer", "?"],
  ["/question", "Question Detail", "✓"],
  ["/review", "Review Center", "◈"],
  ["/chapters", "Chapters & Topics", "≡"],
  ["/practice", "Practice", "▶"],
  ["/practice/session", "Practice Session", "◷"],
  ["/practice/results", "Practice Results", "↗"],
  ["/analytics", "Analytics", "⌁"],
  ["/search", "Search", "⌕"],
] as const;

export function AppChrome({ title, children }: { title: string; children: ReactNode }) {
  const location = useLocation();
  const [open, setOpen] = useState(false);
  return (
    <div className="app">
      <aside className={open ? "side open" : "side"}>
        <div className="brand"><b>M</b><span><strong>ModuleIQ</strong><small>Knowledge workspace</small></span></div>
        <div className="workspace">● &nbsp;Personal workspace　⌄</div>
        <nav aria-label="Primary">
          {items.map(([to, label, icon]) => (
            <NavLink key={to} to={to} onClick={() => setOpen(false)} className={({ isActive }) => isActive ? "nav active" : "nav"}>
              <i>{icon}</i>{label}
            </NavLink>
          ))}
        </nav>
        <div className="side-bottom">
          <div className="profile"><b>S</b><span>My workspace<small>Local-first</small></span></div>
        </div>
      </aside>
      <div className="page">
        <header>
          <button className="hamb" aria-label="Open navigation" aria-expanded={open} onClick={() => setOpen((value) => !value)}>☰</button>
          <div><small>Workspace /</small><b>{title}</b></div>
          <div className="top"><NavLink to="/search" className="search top-link">⌕ <span>Search knowledge...</span><kbd>⌘ K</kbd></NavLink><button aria-label="Help">?</button><b className="avatar">S</b></div>
        </header>
        <main>{children}</main>
      </div>
    </div>
  );
}
