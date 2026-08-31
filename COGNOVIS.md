# cognovis/aidbox-ts-sdk

This is a long-lived Cognovis fork of [HealthSamurai/aidbox-ts-sdk](https://github.com/HealthSamurai/aidbox-ts-sdk) — the TypeScript SDK for Aidbox / FHIR servers.

## Branch model

**`master` is our own fully integrated main.** Everything we build is merged there, and we release from there. It is explicitly **not** a mirror or a clean abstract of `upstream/master`: it carries upstream plus every contribution of ours that upstream has not merged yet.

`cognovis/next` is **not** used — not as a working branch, not for integration, not as a release source. It exists only as history.

| Branch | Purpose |
|---|---|
| `master` | Our integrated main. Contribution branches are merged here; the bridge package is built from here. |
| `feat/<bead>/<slug>`, `fix/<bead>/<slug>` | One capability or fix each, cut from `upstream/master` so the upstream pull-request diff stays focused. Merged into `master` and simultaneously proposed upstream. |

Cutting a contribution branch from `upstream/master` is a pull-request hygiene rule so Health Samurai sees a small, reviewable diff. It says nothing about the role of our `master`. Never fast-forward `master` onto `upstream/master` as if it were a mirror.

Syncing upstream into our main is an ordinary merge:

```bash
git fetch upstream
git checkout master
git merge upstream/master     # never --ff-only, never a reset
```

When Health Samurai merges one of our contributions, the upstream commit supersedes our own copy of it at the next such sync.

## Why we fork

We consume this SDK from two production contexts — the [mira](https://github.com/cognovis/mira) API and the Polaris adapter layer — and want to:

1. **Consolidate** hand-rolled Aidbox clients onto one shared client.
2. **Contribute back** everything vendor-neutral as upstream pull requests.
3. **Stay unblocked** while those pull requests are in review, by releasing our integrated `master` as a temporary package.

Track record: [PR #92](https://github.com/HealthSamurai/aidbox-ts-sdk/pull/92) (`$sql`, `$materialize`, flexible operations) merged cleanly.

## Upstream contribution workflow

1. Cut `feat/<bead>/<slug>` or `fix/<bead>/<slug>` from `upstream/master` — never from `master`, so the pull request stays focused.
2. Implement with tests, review, and verify against a live Aidbox.
3. Merge the branch into `master` (our integrated main).
4. Open the pull request: `gh pr create --repo HealthSamurai/aidbox-ts-sdk --base master --head cognovis:<branch>`.
5. Record base commit, branch, commit SHA and pull-request URL on the owning Bead.
6. After upstream merges, sync `upstream/master` into `master`; our copy of the commit is superseded.

Fork-only changes (bridge publication config, this document) live on `master` alone and are never part of a contribution branch.

## Bridge package

While contributions are in review, `master` is published as `@cognovis/aidbox-client-upstream` to `https://npm.cognovis.de` so consumers can use the capabilities before upstream ships them. The bridge is an immutable prerelease built from one full `master` commit, recorded together with its source commit and the upstream pull-request references. It is removed once an official `@health-samurai/aidbox-client` release provides the same capability floor.

Lifecycle and removal gate are owned by Bead `aidbox-ts-sdk-dfp`; the consumer contract is owned by `fsdk-1hw` in `fhir-sdk`.

## Project state

Tracked in `.beads/` (Dolt-backed). The fork is active: see the Beads labelled `initiative:canonical-fhir-client`.

## Contact

Technical: Malte Sussdorff (malte.sussdorff@cognovis.de) — also on Health Samurai Zulip.
