# Handoff: work the accounts-and-identity map

**Date:** 2026-10-24  **Repo:** `at-auth` (container `algo-trainer`, five sub-repos under `SegFault2017/`)

## Where things stand

The auth effort is charted as a wayfinder map and one ticket is on the frontier.

- Map: https://github.com/SegFault2017/at-auth/issues/1 — **read it first.** Its Notes hold the eleven decisions settled while charting (keep Clerk + `at-auth`, anonymous use stays, lazy upsert replaces `/auth/sync`, only `at-auth` verifies tokens, SQLite default, port 8002, no route middleware, Clerk prebuilt header widgets, Clerk test mode for dev) and six defects recorded as spec requirements. Do not re-derive these.
- Closed: #2 (Clerk token claims), #3 (Clerk middleware), #4 (adopt `at-auth`), #5 (username: dropped; Learner is `sub` + `email`), #6 (problem-set generation: deterministic tutor endpoint; topic tags must flow end to end), #7 (sign-up fails under the isolation headers while Clerk bot protection is on; works with it off), #8 (bot protection stays off; Account Portal is the upgrade path; spec carries a Clerk instance checklist). Each holds its answer in a resolution comment; the map's Decisions-so-far gists them.
- Research findings, pushed and never merged: `research/clerk-token-claims` in `at-auth` (`docs/research/clerk-token-claims.md`), `research/clerk-middleware` in `at-frontend` (`docs/research/clerk-middleware.md`).
- Destination: a `ready-for-agent` spec issue, then per-repo slicing, same shape as the learner-loop spec (at-frontend#10). When the frontier empties, hand off to `/to-spec`.

## Next focus

Take the last frontier ticket:

1. #9 **What does an Attempt record from a Submit?** (grilling, HITL). Graduated from the map's last fog once the Submit result shape was found decided and implemented (`at-frontend/src/lib/api.ts` `SubmitResult`). After it closes the fog is empty: hand off to `/to-spec`.

Facts for #9: the frontend records an Attempt only on an accepted Submit, with `attempts: 1` and `passed_core_tests: true` hardcoded and `topic_tags: []` (the tags fix is already decided in #6). Mastery's clean-solve rate is `hints_used == 0 and attempts == 1`, so retries are invisible today. Both pages build the payload (`src/app/page.tsx`, `src/app/problemset/page.tsx`).

Wayfinder's one-ticket-per-session rule: this session resolved six tickets and the context is long, so start #9 in a fresh session.

Working a ticket: claim it (`gh issue edit <n> -R SegFault2017/at-auth --add-assignee SegFault2017`) before any work, resolve with a comment, close, append one line to the map's Decisions-so-far, graduate any fog.

## Things not in the issues

- **Tracker routing:** never run `gh` against the container repo; always `-R SegFault2017/<repo>`. The previous map used native sub-issues and `dependencies/blocked_by`; this map does too.
- **Git push:** `origin` here is HTTPS (fresh clone); the container and other sub-repos are SSH and this machine has no GitHub SSH access. Push with `git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push https://github.com/SegFault2017/<repo>.git <branch>`. Nothing in git config was changed.
- **Container `.gitignore` lacks `/at-auth/`**, so the clone shows as untracked in `algo-trainer`. The agent's rules forbid editing ignore files; the user was asked to add the line. Never `git add -A` in the container.
- **Frontend state (uncommitted in `at-frontend`):** a test-only "Test: Sign out" button in the home page header (`src/app/page.tsx`, `src/components/AuthProvider.tsx`), marked with a `ponytail:` comment; Clerk's `UserButton` replaces it per the map. `at-frontend/.env.local` holds the Clerk publishable key (user-created; never read it). A stale Turbopack cache sits at `at-frontend/.next.stale-1792884668`; delete it when convenient. `npm install` has now run, so `@clerk/*` is present. Clerk dev instance: bot sign-up protection off, session token customized with `email`.
- **Dev server:** `npm run dev -- -p 3000` in `at-frontend` was still running at handoff, as a background task of the previous session. If port 3000 is busy, find it with `ss -ltnp | grep 3000` and kill the real pid; `pkill` by name missed it once. The home page shows "Failed to fetch" unless the tutor is on :8000, and a Chrome extension adds unrelated "message channel closed" console errors.
- **Local env facts:** `at-auth` has no `.env`; `at_user.db` exists locally and is now ignored. No port pinned; run `uvicorn app.main:app --reload --port 8002`. `PyJWT` installed system-wide is 2.7.0 vs the repo's `>=2.8.0` pin. Tests: `pytest -v` (in-memory SQLite, mock auth backend). Mongo for the other services is the container `algo-scraper-mongo-1` on :27017.
- **Known code defects** (listed on the map, fix via the spec, not ad hoc): no CORS middleware; `POST /problemsets` trusts body `user_id`; `/auth/sync` trusts body email; `verify_aud` off; frontend never calls `/auth/sync`; frontend's `userClient.ts` still defaults `at-auth` to 8001.
- **Vocabulary:** `CONTEXT.md` here and `CONTEXT-MAP.md` in the container define **Attempt** (not "session"), Learner, Mastery, Problem Set. Use them in ticket titles and resolutions.

## Preferences observed

- No co-author trailers on commits (user's global CLAUDE.md overrides the harness reminder, even though the reminder changed with each model switch this session).
- Confirm before networking or paid commands; never read or print `.env`; never edit `.gitignore` or other ignore/security files.
- User answers grilling rounds with "go with your recommendations"; for choices between named options they pick one explicitly.
- Ponytail mode was active: shortest working diff, no speculative abstractions.

## Suggested skills

- `mattpocock-skills:wayfinder` with the map URL to take the next ticket.
- `mattpocock-skills:grilling` and `mattpocock-skills:domain-modeling` for #9 (the map's Notes require both).
- `mattpocock-skills:research` only if a new fact gap appears; the Clerk questions are already answered on their branches.
- `/to-spec` once #9 closes and the map's fog is empty; publish the spec as `ready-for-agent`, then slice per repo.
