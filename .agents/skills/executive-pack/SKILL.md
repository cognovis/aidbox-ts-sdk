---
name: executive-pack
description: Own an approved repository delivery in the invoking session, from Bead admission through review and Session Close.
tracking: git-local
requires_standards: [executive-pack, workflow/uat-config-schema, dispatch/model-routing]
requires:
  - skill:bead-execution-loop
  - skill:context-discovery
  - skill:playwright-cli
  - skill:session-close
  - agent:bead-implementer
  - agent:uat-validator
  - agent:focus-review-agent
  - agent:plan-reviewer
  - agent:doc-changelog-updater
  - standard:executive-pack
scripts:
  - path: scripts/landing_policy.py
    role: helper
    entrypoint: true
    language: python
    output_contract: json-envelope
  - path: scripts/pack_review_contract.py
    role: helper
    entrypoint: false
    language: python
    output_contract: json-envelope
compatibility: {}
metadata: {}
---

# Repository Delivery

Consumer-owned helpers are in `scripts/` of the **installed** skill root, not
the marketplace source path `skills/executive-pack/`. Resolve `$SKILL_ROOT`
local-first and fail closed if none of these exist:

1. `<repo>/.agents/skills/executive-pack`
2. `<repo>/.claude/skills/executive-pack`
3. `<repo>/skills/executive-pack`
4. `~/.agents/skills/executive-pack`
5. `~/.claude/skills/executive-pack`

Helpers include claim normalization, quick-fix and live-network checks, effort
classification, workspace guards, Phase 14 scope, the landing-policy resolver,
and the plan-review gate.

Own one approved repository delivery in this invoking session. `solo` admits exactly
one Bead; `executive-pack` admits an ordered Bead list in one repository. The normal
shape uses one linked worktree. An optional Sub-Pack shape adds isolated execution
worktrees around one parent integration worktree without creating nested repository
deliveries. A direct skill invocation and a launcher-created initial prompt enter this
same repository delivery contract. Never spawn or rename a delivery-owner agent.

STATUS: BEHAVIORAL ROLE AND REVIEW POLICY. The initiating prompt names actors in a
readable role paragraph. The delivery owner follows that paragraph and the applicable review reference. Transport can prove that a distinct session ran, but routing tables or
deterministic model-selection machinery do not interpret the paragraph.

## Admission

Validate the explicit mode, repository, linked worktree, unique ordered Beads,
dependency readiness, proposed TDD seams and prerequisite evidence. Derive seams
from approved AC/MoC; ask only when an unresolved boundary changes scope or risk.
Preserve explicit authorization for the same concrete work and local repairs.
Freeze this contract for the current delivery; edits to it do not change this run.

Name the implementation owner, Reviewer 1, Reviewer 2 and fallback in one role
paragraph, preserving distinct actors and required different-family final review.
Missing actors or incomplete answers never imply approval. The invoking session
owns claims, sequencing, finding disposition, callbacks and Session Close. The
same logical implementation owner owns all source and repairs; reviewers are read-only.
Its current session changes only through the compact committed handoff in
[compact-handoff.md](references/compact-handoff.md). This internal handoff needs no
human approval. The logical implementation owner remains distinct from the delivery
owner and reviewers, and exactly one current implementation session may write.
An optional plan-reviewer advises on an admitted plan and grants no authority.

Before dispatch read [admission.md](references/admission.md). Call
scripts/claim_admission.py admit and scripts/landing_policy.py resolve; use their
typed envelopes, not process exit alone or a prose reconstruction of policy. Record
the exact Beads, candidate, branches, worktree owner and session identity. Provider
worktree ownership is declared, never guessed from paths.

## Implement members

For each ordered bead, claim successfully before invoking bead-execution-loop. Start
the first fresh implementation session from the compact admission packet; later fresh
sessions start from the preceding compact committed handoff. Disable parent history
inheritance (`fork_turns="none"` where the native dispatch supports it). The same
logical implementation owner retains source, TDD, focused MoC and commit responsibility.
Within a large bead, rotate again after a clean committed handoff before the working
context stops being compact.

Use `ccore agent` for implementation dispatch when that transport is selected; a
native subagent is also valid. Both receive the same compact input and distinct-writer
constraints.

Dispatch a fresh Reviewer 1 context for every member. Give it the live Bead, focused
evidence, and the member diff plus affected interactions identified by relevant paths
and evidence. Those paths are review starting points; the reviewer may inspect other
impacted code independently. Disable parent history inheritance for the reviewer. Send
accepted findings back to the logical implementation owner in its
current session, verify focused repairs, then advance without an immediate repeated
full review. Earlier member diffs remain covered by the final whole Pack review.

Only for a requested Sub-Pack shape: read
[subpack-progression.md](references/subpack-progression.md) and
[subpacks.md](references/subpacks.md), then call scripts/subpack_contract.py admit
before dispatch. Delegated Sub-Pack owners sequence, but do not implement, review,
finalize or invoke Session Close; distinct member actors and a parent repair owner
retain those boundaries.

## Review and complete

After the final member and repository gates, read
[final-review.md](references/final-review.md). It defines candidate-bound acceptance,
Reviewer 2, security and project-specific perspectives, allowed not-applicable
evidence and repair convergence. Call scripts/pack_review_contract.py for its evidence
seams. Do not drop required perspectives because this entry is shorter.

After clean final evidence and focused verification, invoke the installed
session-close skill exactly once in this session for all delivery beads and the parent worktree.
Use ccore session-close --help for the live interface and the landing-policy result
for authority. Never use a skill-bundled fallback when ccore is absent.

Resume only the returned Session Close ID. Internal review/repair records remain
caller-owned and are not a Session Close input. Do not duplicate CLI transitions.
The outer result is a concise blocker, review-pending handoff or terminal
result with canonical-main SHA and Session Close ID. Publication alone is not terminal
success; honor human merge authority and report any still-open review gate.
Cross-repository Topic scheduling and callbacks remain outside this skill.

## Usage evidence

Report observed development usage as separate `uncached_input`, `cached_input`, and
`output` values. When transport telemetry does not expose one of those classes, report
that value as `unavailable`; do not estimate it. Do not add cached input to an already
cache-inclusive input total, and do not use usage reporting as a budget or approval
gate.
