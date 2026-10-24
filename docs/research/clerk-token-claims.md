# Clerk session token: claims, and how `email` / `username` get into it

Research for [at-auth#2](https://github.com/SegFault2017/at-auth/issues/2). Sources are Clerk's own docs (clerk.com/docs, fetched 2026-10-24) plus PyJWT source. Consumer: `app/auth/clerk.py` (`verify_aud: False`, reads `sub` and `email`); caller: at-frontend `useAuth().getToken()` with no template.

## 1. What the default session token carries

Version 2 is the current format (v1 deprecated 2025-04-14). Default claims, which "cannot be overridden by templates":

| Claim | Meaning (per Clerk) |
|---|---|
| `azp` | "The `Origin` header that was included in the original Frontend API request made from the user." May be omitted "if, for privacy-related reasons, `Origin` is empty or null." |
| `exp`, `iat`, `nbf` | Standard; `exp` from the Token lifetime setting, `nbf` from Allowed Clock Skew. |
| `iss` | "The Frontend API URL of your instance." Dev instances live on a domain ending in `accounts.dev`; prod is a CNAME subdomain of your app, e.g. `clerk.example.com`. |
| `jti` | Unique token ID. |
| `sid` | Session ID. |
| `sub` | "The ID of the current user of the session." |
| `fva` | Factor verification age `[first, second]` in minutes; `-1` = never. |
| `v` | Token version, `2`. |
| `pla`, `fea`, `sts` | Active plan, enabled features, session status (`pending` etc.). |
| `o` | Organization object (`id`, `slg`, `rol`, `per`, `fpm`); only when an org is active. |
| `act` | Impersonation actor; only during impersonation. |

**Not present by default: `aud` and `email`.** Neither appears anywhere on the session-tokens page or the manual-verification page. Clerk's own `verifyToken()` only checks `aud` if you pass an `audience` option.

Sources:
- https://clerk.com/docs/guides/sessions/session-tokens
- https://clerk.com/docs/guides/sessions/manual-jwt-verification
- https://clerk.com/docs/guides/development/managing-environments
- https://clerk.com/docs/reference/backend/verify-token

## 2. Custom JWT template

Dashboard > **JWT templates** > **New template** (or CLI: `npx clerk@latest api jwt_templates`). A template has a unique **name**, a **token lifetime** (default 60 s), **allowed clock skew** (default 5 s) and a **Claims** JSON object. Shortcodes are substituted at generation time and keep the source type:

```json
{
  "email": "{{user.primary_email_address}}",
  "username": "{{user.username}}"
}
```

- `{{user.primary_email_address}}` is in the current shortcode list (alongside `user.id`, `first_name`, `last_name`, `full_name`, `primary_phone_address`, `email_verified`, `phone_number_verified`, `image_url`, `created_at`, `public_metadata`, `unsafe_metadata`, with `||` fallbacks).
- `{{user.username}}` is **not in the current docs page's inline list**; it is documented only in the 2022-04-22 changelog ("The `{{user.username}}` shortcode has been added to JWT templates"). Treat as supported but confirm in the dashboard editor before relying on it. Note `username` can be `null` for a user who signed up without one unless the instance requires usernames.
- Reserved and auto-included in template tokens: `azp, exp, iat, iss, jti, nbf, sub`. Session-tied claims `sid, v, pla, fea` are **not** included in template tokens; Clerk says to use a customized session token if you need session data.
- `aud` is not reserved, so a template may set a static `"aud": "at-auth"`.
- **Free plan:** the pricing page lists both "Custom session tokens" and "Custom JWT templates" as included on Hobby (free). Only custom session *duration* is paid-gated (Hobby fixed at 7 days).

Sources:
- https://clerk.com/docs/guides/sessions/jwt-templates
- https://clerk.com/changelog/2022-04-22
- https://clerk.com/pricing

## 3. `getToken({ template })` on the client

`function getToken(options?: GetTokenOptions): Promise<null | string>` from `useAuth()` / `Session`. "Tokens can only be generated if the user is signed in" (null otherwise). Options: `template?: string` (dashboard template name), `organizationId?: string`, `skipCache?: boolean` (default false, "force a call to the server instead, even within the TTL").

Caching: "This method uses a cache so a network request will only be made if the token in memory has expired. The TTL for a Clerk token is one minute." It retries transient failures and throws `ClerkOfflineError` when offline. The same behaviour applies to the template path, so a claim change (new username) can be up to ~60 s stale unless `skipCache: true`.

Server side, the Backend SDK `sessions.getToken(sessionId, template?, expiresInSeconds?)` wraps `POST /sessions/{session_id}/tokens/{template_name}`.

Sources:
- https://clerk.com/docs/react/reference/objects/session#gettoken
- https://clerk.com/docs/nextjs/reference/hooks/use-auth
- https://clerk.com/docs/reference/backend/sessions/get-token

## 4. Session token customization vs a named template

Dashboard > **Sessions** > **Customize session token** > **Claims** editor; same shortcode syntax (CLI example: `npx clerk@latest config patch --json '{"session":{"claims":{"fullName":"{{user.full_name}}","primaryEmail":"{{user.primary_email_address}}"}}}'`). Constraints: the session token is also a cookie, so "the cookie can support up to 1.2KB of custom claims" and exceeding it breaks the app; "Clerk refreshes the session token every 60 seconds," so a claim can be a minute stale. The customized claims are part of *the* session token, i.e. what `getToken()` with no template returns and what Clerk's own SDKs read via `sessionClaims`.

**Better fit for at-auth: session token customization.** Reasons:
- Zero frontend change: at-frontend already calls `getToken()` with no template.
- One token serves Clerk's SDK (`auth()`/`sessionClaims`) and at-auth; no second signed token per request.
- Keeps `sid`/`sts`, which template tokens drop.
- Two tiny claims (`email`, `username`) are nowhere near 1.2KB.

A named template only wins if you need a different `aud`/lifetime per downstream service or must keep the session cookie minimal.

Sources:
- https://clerk.com/docs/guides/sessions/customize-session-tokens
- https://clerk.com/docs/guides/sessions/session-tokens

## 5. Development-instance test mode

- "Every development instance has **test mode** enabled by default." It can be turned on in production but "this is highly discouraged."
- Test email: any address with the `+clerk_test` subaddress, e.g. `jane+clerk_test@example.com`; no email is sent, use code `424242`.
- Test phones: `+1 (XXX) 555-0100` to `+1 (XXX) 555-0199`, same code.
- Development instances are capped at 100 users; data does not transfer to production.

Sources:
- https://clerk.com/docs/testing/test-emails-and-phones
- https://clerk.com/docs/guides/development/managing-environments

## 6. PyJWT `verify_aud`

PyJWT `_validate_aud` (jwt/api_jwt.py): with `audience=None` it passes when the token has no/empty `aud` and raises `InvalidAudienceError` if `aud` is present; with `audience="x"` it raises `MissingRequiredClaimError("aud")` when the token has no `aud`.

Consequences for the default Clerk token (no `aud`):
- `verify_aud=True` with no `audience` kwarg is a no-op today, but would start rejecting tokens if an `aud` claim is ever added. Safe but pointless.
- Passing `audience=...` requires first adding `"aud": "<value>"` to the session token (customize) or template; `aud` is not a reserved claim. Use a stable string such as `at-auth`.
- What Clerk actually tells you to verify: signature (RS256 via JWKS at `<FAPI>/.well-known/jwks.json`), `exp`, `nbf`, and `azp` against an allowlist of your origins. PyJWT can do `issuer=<Frontend API URL>` natively; `azp` is a manual check.

Sources:
- https://pyjwt.readthedocs.io/en/stable/usage.html#audience-claim-aud
- https://clerk.com/docs/guides/sessions/manual-jwt-verification

## What this means for the lazy upsert in `get_current_user`

Add `email` (`{{user.primary_email_address}}`) and `username` (`{{user.username}}`) under Dashboard > Sessions > Customize session token; at-frontend keeps calling `getToken()` unchanged. In `ClerkAuthBackend.verify_token` read `sub`, `email`, `username` and, optionally, `azp`/`iss` against config; drop `/auth/sync` and upsert on `provider_id`. Handle `username` being null/absent (require usernames in the Clerk instance or derive a fallback) because the `users.username` column is unique and non-null. Leave `verify_aud` as is unless an `aud` claim is added, in which case pass `audience="at-auth"`. All of this is on the free plan.
