# ModuleIQ Android APK

ModuleIQ is packaged as an Android shell around the same PWA.

## Runtime modes

Local Android uses the bundled PWA with FastAPI at `http://127.0.0.1:8000`. The APK build sets the API origin explicitly for loopback.

Hosted deployments can set `VITE_API_BASE_URL` to an HTTPS API origin, or leave it empty when frontend and API share the same origin.

The APK never contains an AI API key. Provider credentials remain in the backend credential store.

## Build

The Android workflow builds the PWA, generates the Capacitor project, synchronizes web assets, builds a debug APK, validates the archive, and uploads it as an artifact.

## Network security

HTTP is opt-in for local loopback builds through `CAPACITOR_ALLOW_CLEARTEXT=true`. Remote deployments should use HTTPS.
