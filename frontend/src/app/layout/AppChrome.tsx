import { NavLink, useLocation } from "react-router-dom";
import type { ReactNode } from "react";

const items = [
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
  return (
    <div className="app">
      <aside className="side">
        <div className="brand"><b>M</b><span><strong>ModuleIQ</strong><small>Knowledge workspace</small></span></div>
        <div className="workspace">● &nbsp;Personal workspace　⌄</div>
        <nav aria-label="Primary">
          {items.map(([to, label, icon]) => (
            <NavLink key={to} to={to} className={({ isActive }) => isActive ? "nav active" : "nav"}>
              <i>{icon}</i>{label}
            </NavLink>
          ))}
        </nav>
        <div className="side-bottom">
          <NavLink to="/settings" className={({ isActive }) => isActive ? "nav active" : "nav"}>⚙ Settings</NavLink>
          <div className="profile"><b>S</b><span>My workspace<small>Local-first</small></span></div>
        </div>
      </aside>
      <div className="page">
        <header>
          <button className="hamb" aria-label="Open navigation">☰</button>
          <div><small>Workspace /</small><b>{title}</b></div>
          <div className="top"><NavLink to="/search" className="search top-link">⌕ <span>Search knowledge...</span><kbd>⌘ K</kbd></NavLink><button aria-label="Help">?</button><b className="avatar">S</b></div>
        </header>
        <main>{children}</main>
      </div>
    </div>
  );
}
