# at-auth

Learner identity and record for the Algo Trainer app. Verifies Clerk session tokens and
stores who the learner is and what they have attempted.

## Language

**Attempt**:
One learner, one problem, one timed try, with its outcome and the hints used. Shared with
the frontend; defined in the container's `CONTEXT-MAP.md`. Stored in the table still
named `sessions`.
_Avoid_: session (taken by the Clerk login session and the `leetcode_session` cookie),
solve (reads as success)

**Learner**:
The person signed in through Clerk, as `at-auth` knows them: a `users` row keyed by the
Clerk `sub` claim, with the primary email as the fallback identity across a Clerk
re-signup. `at-auth` holds no name or username; Clerk owns display identity.
_Avoid_: account, customer, user (as a domain term; `users` is only the table)

**Mastery**:
Per-topic aggregate over a learner's completed Attempts: count, average time, average
hints, clean-solve rate, last solved.
_Avoid_: progress, stats

**Problem Set**:
A generated list of problems with per-problem time limits that a learner works through
in one mode (`drill` or `interview_sim`).
_Avoid_: playlist, assignment
