# cognovis/aidbox-ts-sdk

> Status: dormant as of 2026-04-20.
>
> Active work on this fork is paused. The current direction keeps adapter and builder work inside the Polaris monorepo and focuses shared infrastructure effort on `cognovis/codegen` plus `fhir-de` builder stabilization. Re-open this initiative only if duplicated Aidbox client logic across multiple consumers becomes a concrete maintenance burden again.

This is a long-lived cognovis fork of [HealthSamurai/aidbox-ts-sdk](https://github.com/HealthSamurai/aidbox-ts-sdk) — the TypeScript SDK for Aidbox / FHIR servers.

## Why we fork

We consume aidbox-ts-sdk (or want to) from two production contexts — the [mira](https://github.com/cognovis/mira) API and the [Polaris / mira-adapters](https://github.com/cognovis/mira-adapters) external integration layer — both of which currently run hand-rolled Aidbox clients. We want to:

1. **Consolidate** the two hand-rolled clients onto upstream aidbox-ts-sdk + a shared extension layer.
2. **Add profile-aware CRUD** ("Layer B") that orchestrates aidbox-client + [@atomic-ehr/codegen](https://github.com/atomic-ehr/codegen)-generated profile classes.
3. **Contribute back** everything vendor-neutral (auth providers, pagination helpers, profile-aware client) as upstream PRs.

Track record: our [PR #92](https://github.com/HealthSamurai/aidbox-ts-sdk/pull/92) (`$sql`, `$materialize`, flexible operations) merged cleanly. Upstream already has `// FIXME: sansara#6557 Generate from IG` flagging the profile gap — the work we plan to contribute is a feature they want.

We fork-first so we can **ship in production on our fork while upstream PRs go through review**, rather than blocking on upstream. Once our additions land upstream and the upstream API stabilises for our use cases, consumers migrate off the fork.

## Scope

**In scope** — work that lives in this fork:
- Auth providers missing upstream (OAuth2 client_credentials with token caching).
- Utility layers (auto-pagination, SSRF URL validation, `materialize(name)` variant).
- Bulk operation wrappers (`$import` / `pollImportStatus`).
- **Profile-aware CRUD (Layer B)** — `AidboxClient.withProfile<T>()` / `ProfileClient<T>` orchestration over [codegen](https://github.com/cognovis/codegen)-generated profile classes.
- Anything else that closes the gap between our two hand-rolled clients and upstream aidbox-client.

**Out of scope**:
- FHIR codegen machinery — that lives in [cognovis/codegen](https://github.com/cognovis/codegen). This fork *consumes* codegen output (profile classes); it does not generate them.
- Aidbox server-side concerns (AccessPolicy authoring, Aidbox Forms, Multibox) unrelated to the client SDK.

## Branch model

| Branch | Purpose | Sync |
|---|---|---|
| `master` | Pure mirror of [HealthSamurai/aidbox-ts-sdk `master`](https://github.com/HealthSamurai/aidbox-ts-sdk/tree/master). Never commit directly; always fast-forward from upstream. | `git fetch upstream && git checkout master && git merge --ff-only upstream/master && git push origin master` |
| `cognovis/next` | Our working / integrating branch. All fork-specific features and infra (this file, `.beads/`) live here on top of `master`. | Rebase onto `master` when syncing with upstream. |
| `cognovis/<consumer>` | Consumer snapshot branches (e.g. `cognovis/polaris`, `cognovis/mira`) — rebase from `cognovis/next`, add consumer-specific scaffolding if needed (built output, consumer-pinned configs). | Rebase from `cognovis/next` before pinning consumers. |
| `fix/<slug>`, `feat/<slug>` | Short-lived branches cut from pristine `master` for upstream PRs. Never base these on `cognovis/next` — keep the PR diff focused. | Delete after upstream merge or close. |

### Current long-lived branches

- `master` — upstream mirror, currently at `746c422`.
- `cognovis/next` — upstream + fork-specific docs / Beads context.

## Consumer integration

Consumers pin via git URL to a stable consumer branch. The current plan (TBD based on how `dist/` / build output shapes up):

```json
{
  "dependencies": {
    "@health-samurai/aidbox-client": "github:cognovis/aidbox-ts-sdk#cognovis/<consumer>"
  }
}
```

Consumer branches commit pre-built output if `prepare` hooks don't cut it (bun doesn't install a git dep's devDependencies — see the equivalent workaround in [cognovis/codegen `cognovis/mira-adapters`](https://github.com/cognovis/codegen/tree/cognovis/mira-adapters) for the pattern).

## Upstream PR workflow

1. Branch `fix/<slug>` or `feat/<slug>` from `master` — **not** `cognovis/next`. Upstream sees a clean, focused diff.
2. Implement + test. Commit with conventional-commit message.
3. Rebase `cognovis/next` on top to pick it up locally.
4. `gh pr create --repo HealthSamurai/aidbox-ts-sdk --head cognovis:<branch>`.
5. When upstream merges (squash or rebase), delete the branch. On next upstream sync, `cognovis/next` rebases cleanly and our version of the commit drops out.

For fork-only changes (e.g. `dist/` on consumer branches, opinionated API surface not yet proposed upstream), document in the commit message: `fork-only: <reason>`.

## Upstream sync

```bash
# 1. Sync master to upstream
git checkout master && git fetch upstream && git merge --ff-only upstream/master && git push origin master

# 2. Rebase cognovis/next onto updated master
git checkout cognovis/next && git rebase master

# 3. Re-run tests + build
bun test && bun run build

# 4. Rebase each cognovis/<consumer> onto updated cognovis/next
git checkout cognovis/polaris && git rebase cognovis/next
git push --force-with-lease

# 5. Notify consumers to `bun update`
```

These upstream-sync notes are retained as historical reference only; there is no active sync-runbook work while the fork is dormant.

## Project state & roadmap

Tracked in `.beads/` (Dolt-backed).

Current state:

- This fork is retained as dormant infrastructure, not an active delivery track.
- `master` remains an upstream mirror and `cognovis/next` keeps the fork-specific context (`COGNOVIS.md`, `.beads/`, prior strategy notes).
- The earlier "consolidate both clients + Layer B" push is preserved as historical context, not the current execution path.

Current execution focus lives elsewhere:

- `cognovis/codegen` — stabilise the fork and improve generator ergonomics.
- Polaris monorepo — keep adapter work colocated and stabilise `fhir-de` builders before revisiting any wider client consolidation.
- mira — continue using its current client path unless and until a renewed consolidation effort is justified by real maintenance cost.

Re-open criteria for this fork:

- At least two consumers are again carrying materially duplicated Aidbox client logic.
- That duplication creates concrete maintenance cost, regressions, or release friction.
- The packaging and consumer-install story for a shared client is proven, not assumed.

## Contact

Technical: Malte Sussdorff (malte.sussdorff@cognovis.de) — also on Health Samurai Zulip for fast back-and-forth.
