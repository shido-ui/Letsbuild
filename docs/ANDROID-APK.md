# ModuleIQ Android APK

ModuleIQ is packaged as an Android shell around the production PWA rather than maintaining a second native UI.

## Runtime

Android APK → bundled ModuleIQ PWA → local ModuleIQ FastAPI backend → SQLite/files → optional AI provider.

The APK does not contain an AI API key.

The bundled UI expects the backend on the same Android device at http://127.0.0.1:8000. The backend remains responsible for persistence, credentials, processing and AI-provider access.

## Build

The Android workflow builds the web app, generates the Capacitor Android project, synchronizes the web assets, builds a debug APK, verifies the APK archive, and uploads it as a GitHub Actions artifact.

## Security

The local HTTP scheme is intentional for loopback communication. Remote production deployments should use HTTPS and an explicit API origin.
