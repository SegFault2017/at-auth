# Handoff: implement the accounts-and-identity slices

**Date:** 2026-10-25  **Repo:** `at-auth` (container `algo-trainer`, five sub-repos under `SegFault2017/`)

## Where things stand

The accounts-and-identity effort has moved from planning to implementation-ready. All grilling is done; the spec is published and sliced into tickets.

- Map `at-auth#1`: **closed**. All eleven decisions and six defects it recorded are now folded into the spec below — don't re-derive them, read the spec instead.
- Spec: https://github.com/SegFault2017/at-auth/issues/10 (`ready-for-agent`) — **read it first.** Full Problem Statement / Solution / 41 User Stories / Implementation Decisions / Testing Decisions / Out of Scope. Source of truth for every slice ticket.
- Sliced into four per-repo tickets, same shape as the learner-loop precedent (at-frontend#10 → #11/#12/#14/#15 in that effort). Each slice body says `Slice of spec at-auth#10 (user stories N-M)` and has its own `## Scope` + `## Tests`/`## Verification`:
  - **`at-auth#11`** — lazy upsert (replaces `/auth/sync`), `Session`→`Attempt` rename (model, table, routes, new field shape), mastery recomputed over the new formula, CORS, port 8002 default. **No dependencies — the natural first pick**, since the frontend ticket needs its new shape to exist.
  - **`at-ai-tutor#14`** — pure `POST /api/problemset/generate` (deterministic, no model call), catalog list/get-by-slug returning `topic_tags`. No dependencies.
  - **`algo-scraper#61`** — publish `topic_tags` alongside problem text and Hidden Tests. No dependencies.
  - **`at-frontend#13`** — sign-in UI (`UserButton`, `oauthFlow="redirect"`), Attempt payload rename, problem-set page becomes the real free-mode workspace with auto-submit on timer expiry. **Depends on all three above.**
- None of the four slice tickets have been started. No implementation code has been written yet.

## Next focus

Start `at-auth#11` (or, if working multiple repos in parallel, `at-ai-tutor#14` / `algo-scraper#61` too — they're mutually independent).

Working a ticket: claim it (`gh issue edit <n> -R SegFault2017/<repo> --add-assignee SegFault2017`) before any work. `superpowers:test-driven-development` fits cleanly — the spec's Testing Decisions section names the exact seam per repo (at-auth: existing ASGI test-client suite with mocked auth backend + in-memory SQLite). Ponytail mode was active all session: shortest diff that satisfies the slice, no speculative abstraction.

`at-auth#11`'s concrete scope, condensed from the ticket:
1. Remove `/auth/sync`; `get_current_user` provisions by subject → email re-key → create; 401 on no `email` claim.
2. `User` drops `username`/`first_name`/`last_name`.
3. Rename `Session`/`sessions` → `Attempt`/`attempts`; `POST /sessions`→`POST /attempts`, `GET /users/me/sessions`→`GET /users/me/attempts`. New field shape is in the ticket (verdict, passed/failed/total, per-Case-Category counts, `submit_index` replacing `attempts`, confidence nullable-except-on-accepted). Drops `passed_core_tests`, `passed_edge_tests`, `hidden_tests_*`, `hint_level_reached`, `time_taken_seconds`, `completed_at`, review-derived fields.
4. Mastery: `clean_solve_rate` over `submit_index==1` rows only; averages/`last_solved_at` over accepted rows only (null if none); failure-only topics still appear.
5. `POST /problemsets` takes user from token, not body `user_id`; drop `problem_sets.status`.
6. Add CORS middleware for the frontend origin; default port 8002.
- Explicitly out of scope for this ticket: `verify_aud` stays off (no code change), SQLite/Postgres already configurable via `DATABASE_URL` (no code change).

## Things not in the issues

- **Tracker routing:** never run `gh` against the container repo; always `-R SegFault2017/<repo>`.
- **`gh issue view` is broken on these repos** — plain `gh issue view <n> -R ...` (with or without `--comments`) fails with a Projects-classic GraphQL error. Always read via `gh issue view <n> -R ... --json title,body,comments -q '...'`. (Saved to memory as `gh-issue-view-needs-json`.)
- **Git push:** `origin` here is HTTPS; this machine has no GitHub SSH access. Push with `git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push https://github.com/SegFault2017/<repo>.git <branch>`.
- **Container repo caution:** earlier this session, something outside this session's own actions committed locally in `algo-trainer` (`ca839f9`), adding `at-auth` as a bare gitlink (no `.gitmodules`) under a different git identity (`ray.tangent42@gmail.com`) than the session's configured one (`raymondt@purposeinvest.com`). It was never pushed (no SSH access) and was undone with `git reset --soft` + unstaging `at-auth` back to untracked, per the user's choice. Cause unidentified — if it recurs, flag it again rather than building on it. Container `.gitignore` still lacks `/at-auth/`; never `git add -A` in the container.
- **`at-auth`'s own `.claude/handoffs/work-the-auth-map-2026-10-24.md`** has a pre-existing staged-but-uncommitted diff from before this session started (visible in `git status` as the only tracked change there besides this new handoff file). It was left untouched both in the prior session and this one — not this effort's concern, don't commit or discard it without asking.
- **Local env facts** (from the prior handoff, still current): `at-auth` has no `.env`; `at_user.db` is local and ignored; run `uvicorn app.main:app --reload --port 8002`; `PyJWT` installed system-wide is 2.7.0 vs the repo's `>=2.8.0` pin; tests via `pytest -v` (in-memory SQLite, mock auth backend). `at-frontend`'s dev server / stale Turbopack cache state from that handoff wasn't re-checked this session — verify before assuming either is still true.
- **Vocabulary**, now sharpened this session: **Attempt** = one learner, one problem, one Submit — the time from opening the problem to that Submit, its verdict, and the hints used by then. A failed Submit is an Attempt; Run is not. Updated in `at-auth/CONTEXT.md` and the container's `CONTEXT-MAP.md` (both committed, `at-auth@7b70287` / `algo-trainer@121d9c7`).

## Preferences observed

- No co-author trailers on commits (user's global CLAUDE.md overrides the harness reminder, which changed wording on every model/effort switch this session).
- Confirm before networking or paid commands; never read or print `.env`; never edit `.gitignore` or other ignore/security files.
- User answers grilling rounds with "go with your recommendations"; for named-option choices they pick one explicitly; for process questions (spec repo, test seams, stray-commit handling) they picked the recommended option each time.
- Ponytail mode (full) was active throughout: shortest working diff, no speculative abstractions, YAGNI by default.
- When something looks anomalous (e.g. a commit this session didn't make), the user wants it surfaced and confirmed before continuing, not silently built on top of.

## Suggested skills

- `superpowers:test-driven-development` for implementing any of the three unblocked slices (`at-auth#11`, `at-ai-tutor#14`, `algo-scraper#61`) — each has an explicit existing test seam named in the spec.
- `ponytail:ponytail` (already the session default) to keep the implementation diff minimal.
- `superpowers:verification-before-completion` before claiming a slice ticket done — run its named test seam and show the output.
- `mattpocock-skills:pr` when a slice's branch is ready, for the PR body.
- `sidekick:handoff` again if the session runs long enough to need a second handoff mid-implementation.
