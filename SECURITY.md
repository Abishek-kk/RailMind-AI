# Security Policy

RailMind AI handles safety and security incident data, video feed metadata, alerts,
and operator workflows. Please report suspected vulnerabilities privately so they
can be triaged before public disclosure.

## Supported Versions

| Version | Supported |
| ------- | --------- |
| v2.0.x  | Yes       |
| < v2.0  | No        |

This repository is currently maintained on the v2.0 release line. Security fixes
are applied to the active branch only unless a maintainer explicitly announces a
backport.

## Reporting a Vulnerability

Do not open a public issue for a vulnerability. Use GitHub's private security
advisory flow for this repository when available, or contact the project
maintainers through the private channel used for TeamAccelerate development.

Include the following details when possible:

- Affected component or endpoint.
- Steps to reproduce.
- Expected impact, including whether incident data, alert state, video uploads,
  model artifacts, API keys, or operator actions are exposed or modifiable.
- Relevant logs, request/response examples, or screenshots with secrets removed.
- Suggested mitigation, if you have one.

Please do not include real passenger footage, production credentials, API keys,
or personally identifiable information in the report. Use synthetic data or
redacted examples.

## Scope

Security reports are especially valuable for:

- Authentication or authorization bypass on `/api/*` endpoints.
- Unauthorized access to incident, alert, feed, staff, analytics, or training
  data.
- Arbitrary file upload, path traversal, or unsafe media handling.
- Remote code execution, SQL injection, cross-site scripting, or server-side
  request forgery.
- Exposure of `.env` values, model artifacts that should remain private, or API
  keys used by optional LLM providers.
- Unsafe training or inference behavior that can be triggered by an untrusted
  request.

Out-of-scope reports include denial-of-service claims that require unrealistic
local access, dependency findings without an exploitable path in this project,
and issues that only affect deliberately mocked demo data.

## Current Prototype Limitations

The v2.0 prototype protects REST API routes with `X-API-Key` and
`RAILMIND_API_KEY`. This is not a full production identity, session management,
or role-based access-control system. Browser builds may expose
`VITE_RAILMIND_API_KEY`, so deployments that handle real operations must place
RailMind behind proper identity-aware access controls before use.
