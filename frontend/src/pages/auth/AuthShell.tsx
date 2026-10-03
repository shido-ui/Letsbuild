import type { ReactNode } from "react";
import type { ReactElement } from "react";

type Props = { title: string; subtitle: string; children: ReactNode };

export function AuthShell({ title, subtitle, children }: Props): ReactElement {
  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="brand-mark">M</div>
        <span className="tag purple">MODULEIQ</span>
        <h1>{title}</h1>
        <p>{subtitle}</p>
        {children}
        <small>Local-first · AI keys stay server-side · Canonical knowledge remains yours</small>
      </section>
    </main>
  );
}
