# ModuleIQ Android runtime

## Architecture

The Android APK is the UI shell. The FastAPI service owns SQLite/local storage and encrypted BYOK credentials. Huey runs ingestion jobs outside the Android WebView.

## Start the complete local backend

From the repository root:

```bash
pip install -e '.[dev,document-engine]'
bash scripts/start-local.sh
```

`scripts/start-local.sh` starts FastAPI on `http://127.0.0.1:8000` and a Huey consumer for `moduleiq.workers.ingestion.huey`. Uploads enqueue jobs and the consumer performs them.

## Connect the APK

Install the signed QA APK from the GitHub Actions artifact and open **Settings → Backend connection**.

- Local Android/Termux backend: `http://127.0.0.1:8000/api`
- Hosted backend: use the HTTPS API base, for example `https://your-host.example/api`.
- Use **Test connection** before saving.

The APK never receives or stores AI provider API keys. Keys are entered through the ModuleIQ Settings UI and remain in the backend credential store.

## Release signing

The completion workflow creates a signed **QA** APK with an ephemeral CI certificate so the artifact is installable for testing. This is not the permanent production signing key. A real public release should use a privately controlled release keystore and keep that key outside the repository.

## Runtime acceptance

Before calling an installation complete, verify: backend health, APK-to-backend connection, PDF upload, queued processing, worker completion, knowledge hierarchy, search, practice, AI provider connection/switch/disconnect, export/import, Android drawer navigation, and reinstall behavior.
