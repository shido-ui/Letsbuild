# Authentication

ModuleIQ API authentication uses OAuth2 password-form login followed by short-lived JWT bearer access tokens.

- Register: POST /api/auth/register
- Login: POST /api/auth/login (form fields: username, password)
- Current user: GET /api/auth/me
- Logout: POST /api/auth/logout
- Protected application APIs require Authorization: Bearer <token>.
- JWT signing configuration is provided by MODULEIQ_SECRET_KEY.
- The test suite may use the explicit test environment bypass for legacy single-user fixtures; production and development do not.
