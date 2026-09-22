## Final Pack perspectives

After the last member and repository gates:

1. Keep current implementation and documentation, invoking `doc-changelog-updater` when
   the delivery carries a material user-visible, API, configuration, deployment,
   operator-workflow, or developer-workflow change.
2. As the delivery owner, capture live claims and the signed resource registry: every
   admitted Bead AC/MoC and current documented capability claim, bound to the candidate.
3. Run agentic acceptance via `ccore acceptance run` through a fresh `uat-validator`
   against those signed resource boundaries. Acceptance applies only where the caller
   trust surface is provisioned: when the canary exits 3 with a
   `status: "not_configured"` result (no `AGENTIC_ACCEPTANCE_*` trust material on this
   host), record that typed result verbatim as explicit not-applicable acceptance
   evidence bound to the candidate and continue with the remaining perspectives — do
   not stop the delivery and do not ask the human to provision trust material.
   Recognize `not_configured` only from the typed canary output written to `--output`,
   never from your own judgment about the environment. On a provisioned host, any
   non-passing acceptance outcome (`failed`, `blocked`, exit 2) blocks delivery. Any source
   repair invalidates the acceptance result and requires a fresh run before those later
   reviews continue. The native first-party validator reaches real interfaces through
   the caller-owned bounded surface broker while authenticated host state and trust keys
   remain outside the validator capsule. For the authoritative acceptance command, run
   `ccore acceptance run --help`. Default transport is `codex-cli`. Use the `acpx`
   transport only with an explicit project `.acpxrc.json`. If `ccore` is absent, stop
   with `ccore_not_installed`; do not scan for or invoke skill-bundled Python files.
4. Run one complete different-family adversarial review by Reviewer 2 over the whole
   Pack base-to-candidate diff, one security review, and every applicable
   project-specific perspective. Each produces distinct
   evidence; `not_applicable` must be explicit where permitted.
   `passed` means no accepted substantive finding remains; `changes_requested` carries
   actionable findings into repair convergence; unavailable or invalid outcomes block.
5. Consolidate accepted Medium-or-higher findings into one implementation-owned repair
   lineage. In normal serial execution, a fresh session may continue that lineage only
   through the compact committed handoff. In the Sub-Pack shape, the fixed
   parent-integration repair session remains the scoped exception. Continue only repair
   and focused verification turns until no accepted substantive finding remains. Do not
   repeat every full perspective after each repair.
6. Interrupt normal progression only for disputed findings, contradictory
   recommendations, suspicious summaries, or intent mismatch. The delivery owner
   returns the typed disposition. Clean consistent evidence bypasses adjudication.

`scripts/pack_review_contract.py` validates these small evidence seams. It never selects
actors, parses role prose, freezes a candidate lifecycle, or exports internal review
state. The signed agentic-acceptance runtime is the installed `ccore acceptance run`
command; this skill does not ship a Python fallback.
