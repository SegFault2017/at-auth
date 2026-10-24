# Handoff: work the accounts-and-identity map

**Date:** 2026-10-24  **Repo:** `at-auth` (container `algo-trainer`, five sub-repos under `SegFault2017/`)

## Where things stand

The auth effort is charted as a wayfinder map and three tickets are on the frontier.

- Map: https://github.com/SegFault2017/at-auth/issues/1 — **read it first.** Its Notes hold the eleven decisions settled while charting (keep Clerk + `at-auth`, anonymous use stays, lazy upsert replaces `/auth/sync`, only `at-auth` verifies tokens, SQLite default, port 8002, no route middleware, Clerk prebuilt header widgets, Clerk test mode for dev) and six defects recorded as spec requirements. Do not re-derive these.
- Closed: #2 (Clerk token claims), #3 (Clerk middleware), #4 (adopt `at-auth`). Each holds its answer in a resolution comment; the map's Decisions-so-far gists them.
- Research findings, pushed and never merged: `research/clerk-token-claims` in `at-auth` (`docs/research/clerk-token-claims.md`), `research/clerk-middleware` in `at-frontend` (`docs/research/clerk-middleware.md`).
- Destination: a `ready-for-agent` spec issue, then per-repo slicing, same shape as the learner-loop spec (at-frontend#10). When the frontier empties, hand off to `/to-spec`.

## Next focus

Take the first open frontier ticket, in this order, one per session:

1. #5 **Username under lazy upsert** (grilling, HITL). Caveat from #2: `{{user.username}}` as a session-token shortcode is only attested in a 2022 changelog; verify in the Clerk dashboard editor or weigh toward deriving/dropping the column. Nothing in the frontend displays username.
2. #6 **Pure problem-set generation contract** (grilling, HITL). Depends on catalog endpoints in SegFault2017/at-ai-tutor#12; not blocked on this map.
3. #7 **Sign-up under COOP/COEP** (task, HITL). Needs a Clerk dev instance, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` locally, and a real `npm install` in `at-frontend` (`node_modules` lacks `@clerk/*`; the earlier `npm ci` ran with install scripts blocked). Confirm with the user before `npm install`.

Working a ticket: claim it (`gh issue edit <n> -R SegFault2017/at-auth --add-assignee SegFault2017`) before any work, resolve with a comment, close, append one line to the map's Decisions-so-far, graduate any fog.

## Things not in the issues

- **Tracker routing:** never run `gh` against the container repo; always `-R SegFault2017/<repo>`. The previous map used native sub-issues and `dependencies/blocked_by`; this map does too.
- **Git push:** `origin` here is HTTPS (fresh clone); the container and other sub-repos are SSH and this machine has no GitHub SSH access. Push with `git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push https://github.com/SegFault2017/<repo>.git <branch>`. Nothing in git config was changed.
- **Container `.gitignore` lacks `/at-auth/`**, so the clone shows as untracked in `algo-trainer`. The agent's rules forbid editing ignore files; the user was asked to add the line. Never `git add -A` in the container.
- **Local env facts:** `at-auth` has no `.env`; `at_user.db` exists locally and is now ignored. No port pinned; run `uvicorn app.main:app --reload --port 8002`. `PyJWT` installed system-wide is 2.7.0 vs the repo's `>=2.8.0` pin. Tests: `pytest -v` (in-memory SQLite, mock auth backend). Mongo for the other services is the container `algo-scraper-mongo-1` on :27017.
- **Known code defects** (listed on the map, fix via the spec, not ad hoc): no CORS middleware; `POST /problemsets` trusts body `user_id`; `/auth/sync` trusts body email; `verify_aud` off; frontend never calls `/auth/sync`; frontend's `userClient.ts` still defaults `at-auth` to 8001.
- **Vocabulary:** `CONTEXT.md` here and `CONTEXT-MAP.md` in the container define **Attempt** (not "session"), Learner, Mastery, Problem Set. Use them in ticket titles and resolutions.

## Preferences observed

- No co-author trailers on commits (user's global CLAUDE.md overrides the harness reminder).
- Confirm before networking or paid commands; never read or print `.env`; never edit `.gitignore` or other ignore/security files.
- User answers grilling rounds with "go with your recommendations"; for choices between named options they pick one explicitly.
- Ponytail mode was active: shortest working diff, no speculative abstractions.

## Suggested skills

- `mattpocock-skills:wayfinder` with the map URL to take the next ticket.
- `mattpocock-skills:grilling` and `mattpocock-skills:domain-modeling` for #5 and #6 (the map's Notes require both).
- `mattpocock-skills:research` only if a new fact gap appears; the two Clerk questions are already answered on their branches.
- `mattpocock-skills:wizard` for #7 if the user wants a guided walk through the Clerk dashboard and local sign-up check.
