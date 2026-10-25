# at-auth

Learner identity and record for the Algo Trainer app. Verifies Clerk session tokens and
stores who the learner is and what they have attempted.

## Language

**Attempt**:
One learner, one problem, one Submit: the time from opening the problem to that Submit,
its verdict, and the hints used by then. A failed Submit is an Attempt; Run is not.
Shared with the frontend; defined in the container's `CONTEXT-MAP.md`.
_Avoid_: session (taken by the Clerk login session and the `leetcode_session` cookie),
solve (reads as success)

**Learner**:
The person signed in through Clerk, as `at-auth` knows them: a `users` row keyed by the
Clerk `sub` claim, with the primary email as the fallback identity across a Clerk
re-signup. `at-auth` holds no name or username; Clerk owns display identity.
_Avoid_: account, customer, user (as a domain term; `users` is only the table)

**Mastery**:
Per-topic aggregate over all of a learner's Attempts, failed ones included. It counts the
Attempts and gives the clean-solve rate, the share of first Submits accepted with no hints.
Average time, average hints and last solved count accepted Attempts only.
_Avoid_: progress, stats

**Problem Set**:
A generated list of problems with per-problem time limits that a learner works through
in one mode (`drill` or `interview_sim`).
_Avoid_: playlist, assignment
