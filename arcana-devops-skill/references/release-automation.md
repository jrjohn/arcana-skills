# Release Automation (release-please + Renovate automerge + auto-publish)

> Distilled from a fleet-wide rollout across 15+ repos (2026-08). The one-line
> failure mode behind every symptom here: **automation opens PRs, but nothing
> merges them.** A green build is not a release; a green dependency PR is not a
> merge. Wire the *merge* step or the pipeline stalls silently.

## 0. The mental model

```
Renovate auto-merges green deps  →  feat/fix lands on main
  →  release-please opens a release PR  →  auto-publish merges it  →  tag + GitHub release
```

Each arrow is a *merge* that must be automated. Jenkins builds/tests/scans — it
**never releases**. release-please cuts releases; Renovate lands deps. If either
"open PR" step has no matching "merge" step, PRs pile up (seen: Spring Boot 4.1.0
green + unmerged for a month; 15 dep PRs stalled fleet-wide; builds green for
2 months with the release stuck at an old tag).

---

## 1. release-please must be *push-triggered*, not hand-run

Symptom: build passes every day, but no new GitHub release appears; the latest
release is months old.

Cause: release-please was bootstrapped (`release-please-config.json` +
`.release-please-manifest.json`) but had **no trigger**, so it only ran when
invoked by hand. Commits pushed straight to `main` never produced a version.

Fix — a GitHub Actions workflow on every push to main (Jenkins can't do this;
it has no release stage):

```yaml
# .github/workflows/release-please.yml
name: release-please
on:
  push:
    branches: [main]
permissions:
  contents: write
  pull-requests: write
jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
```

Manual trigger (before the workflow lands, or to backfill a pending release):
```bash
npx --yes release-please@latest release-pr   --repo-url=OWNER/REPO --token="$(gh auth token)"
npx --yes release-please@latest github-release --repo-url=OWNER/REPO --token="$(gh auth token)"
```
`github-release` cuts a tag whose manifest bump was merged but never tagged — the
classic half-wired symptom (manifest says 1.1.1, but latest tag is 1.1.0).

### Trap A — the repo setting that silently blocks PR creation
The `permissions:` block in the workflow is **not enough**. The repo (or org)
must also have **Settings → Actions → General → "Allow GitHub Actions to create
and approve pull requests"** enabled, or the Action cannot open its release PR.
```bash
gh api -X PUT repos/OWNER/REPO/actions/permissions/workflow \
  -F default_workflow_permissions=read -F can_approve_pull_request_reviews=true
```

### Trap B — `release-type: rust` on a Cargo *workspace*
`release-type: rust` errors `value at path package.version is not tagged` when the
version lives in `[workspace.package]` and there is no root `[package].version`
(the whole build never cuts a release). Use `release-type: simple` — it manages
the manifest + CHANGELOG + tag and does **not** touch `Cargo.toml`. Pick the
updater to match where the version actually is, not the language.

---

## 2. Renovate automerge — the `platformAutomerge` silent-fail

Symptom: Renovate opens dependency PRs, CI goes green, but they never merge and
accumulate.

Cause: the preset had `automerge: true` **and** `platformAutomerge: true`.
`platformAutomerge` uses GitHub's *native* auto-merge, which requires **both**
(a) the repo's "Allow auto-merge" setting ON, **and** (b) branch protection with
a required status check. With neither configured, Renovate cannot enable
auto-merge and does nothing — silently. (Check: `gh pr view N --json autoMergeRequest`
shows no request; `gh api repos/O/R --jq .allow_auto_merge` is false.)

Fix (simplest, no branch-protection setup): **drop `platformAutomerge`** →
Renovate merges green PRs itself via the API. One edit to the shared preset
(`extends: ["github>OWNER/renovate-config"]`) fixes the whole fleet:

```jsonc
{
  "packageRules": [
    { "matchUpdateTypes": ["minor","patch","pin","digest","lockFileMaintenance"],
      "automerge": true },
    { "matchUpdateTypes": ["major"], "automerge": false }   // majors stay manual
  ]
  // no platformAutomerge
}
```

**Keep majors manual.** A *green* major can still break — e.g. `ioredis` v6
auto-merged while `bullmq` v5 required `ioredis` v5; CI stayed green on the
ioredis bump alone, then a later bullmq bump surfaced the break. CI is a safety
net for non-major bumps, not a guarantee that a major is compatible.

---

## 3. Auto-publishing releases — the GITHUB_TOKEN loop-prevention trap

To merge release PRs automatically (full hands-off release), you **cannot** use
the built-in `GITHUB_TOKEN`: a merge performed with `GITHUB_TOKEN` does **not**
trigger other workflows (GitHub loop-prevention), so the tag-cut workflow never
fires → the PR merges but no tag/release is produced. A **PAT**'s merge does
trigger it.

Cleanest pattern — one scheduled workflow in an ops repo, merging green release
PRs across the fleet with a PAT (`RELEASE_PLEASE_TOKEN`, fine-grained: Contents +
Pull requests = write):

```yaml
name: auto-publish-releases
on:
  schedule: [{ cron: '23 * * * *' }]
  workflow_dispatch:
permissions: {}
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - env: { GH_TOKEN: '${{ secrets.RELEASE_PLEASE_TOKEN }}' }
        run: |
          for r in <fleet repos>; do
            R="OWNER/$r"
            pr=$(gh pr list -R "$R" --state open --json number,title,mergeStateStatus \
                  --jq '[.[]|select(.title|startswith("chore(main): release"))|select(.mergeStateStatus=="CLEAN")][0].number // empty')
            [ -n "$pr" ] && gh pr merge "$pr" -R "$R" --squash   # PAT merge → triggers the tag-cut
          done
```

Notes:
- Filter to `mergeStateStatus=="CLEAN"` — **never auto-publish a red release PR**.
  (This correctly withheld a release whose CI was red for an infra reason, not a
  code one — the safety behaviour is right even when the red is a false alarm.)
- Don't use `--admin` unless the PAT has admin + you need to bypass branch
  protection; plain `--squash` keeps the PAT scope minimal.
- **Caveat**: GitHub disables a scheduled workflow after 60 days of no commits to
  the host repo (it emails a warning first); any commit or manual "Run workflow"
  re-arms it.

---

## 4. Triggering / watching a Jenkins build without the SSO front door

When the Jenkins UI is behind an SSO proxy (Authelia), drive it from the host on
`localhost` (the container binds `127.0.0.1:8080`), which bypasses the proxy:

```bash
J=http://localhost:8080/jenkins           # personal Jenkins login: admin/admin
CJ=$(mktemp)
CRUMB=$(curl -s -c "$CJ" -u admin:admin "$J/crumbIssuer/api/json" \
        | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d["crumbRequestField"]+": "+d["crumb"])')
curl -X POST -b "$CJ" -u admin:admin -H "$CRUMB" \
     "$J/job/<mb-job>/job/<PR-N>/build"    # 201 = queued
# build logs on disk: /var/jenkins_home/jobs/<job>/branches/<branch>/builds/<n>/log
```

Watch: poll `.../lastBuild/api/json?tree=number,building,result` until
`building=false`. Note release-please may refresh the release PR's HEAD commit
mid-run — build the *current* head, or the green lands on a stale commit and the
PR stays UNSTABLE.
