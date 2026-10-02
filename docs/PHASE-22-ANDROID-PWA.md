# Phase 22 — Android / PWA

ModuleIQ is installable as a standalone Android-friendly PWA without changing the canonical backend architecture.

- Web App Manifest defines standalone display, portrait orientation, theme/background colors, start URL and app icons.
- Service worker caches the application shell and same-origin static GET responses for offline startup.
- Android/browser metadata is included in the document head.
- The responsive shell already adapts navigation and grids for small screens.
- API requests remain network-backed so the PWA never fabricates knowledge while offline.
- Termux can serve the built frontend locally; the PWA can be installed from the browser and opened as a standalone app.
