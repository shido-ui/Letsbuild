# Phase 28 — GitHub Release

Release infrastructure is prepared for semantic version tags.

- CHANGELOG.md records the consolidated 0.1.0 scope.
- RELEASE_NOTES_v0.1.0.md is the release body.
- The release workflow runs backend migrations/tests and the production frontend build before publishing.
- Publishing is tag-driven and uses the repository GitHub token.
- No release object is claimed as published until a version tag is intentionally pushed.
