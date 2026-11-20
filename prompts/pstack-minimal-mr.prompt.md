---
agent: 'agent'
description: 'Adapt pstack practices for existing Copilot domain agents: reuse team code, keep feature MRs focused, and verify behavior separately from diff size.'
---

# Set up domain ownership and minimal feature MRs

Run this once **inside the work environment** to improve the existing Copilot/OpenSpec harness, not to implement or clean up a product feature. If this runtime does not load `.prompt.md`, paste from this heading to the end. It needs no plugin installation, external document fetch, or other catalog file.

- Target repositories: ${input:repos:Two authorized local workspaces}
- Pilot: ${input:pilot:An existing feature issue, MR, or OpenSpec change with a known review correction}

For pasted text, use the workspaces and pilot named by the user; ask for missing inputs rather than treating placeholders as paths. Keep internal references, code and evidence inside Citrix. Never expose secrets. Start read-only; require approval for each terminal command separately. Do not install or update software, enable hooks/auto-approval, change permissions, access production, commit, push, or open an MR.

## 1. Reuse selected pstack practices, not its shipping workflow

These are original Copilot instructions based on [Lauren Tan's pstack, pinned source](https://github.com/cursor/plugins/tree/aaeb0ea3a0584995aa8f55ce44c6c5259414b896/pstack). If approved equivalents are **already installed and supported**, use the matching local guidance and record its path/version. Do not assume Cursor slash commands work in Copilot. If absent, blocked, or offline, apply the right-hand column directly. The links are for provenance, not prerequisites.

| Upstream guidance | Use here |
| --- | --- |
| [Feature playbook](https://github.com/cursor/plugins/blob/aaeb0ea3a0584995aa8f55ce44c6c5259414b896/pstack/skills/poteto-mode/playbooks/feature.md) | Trace the existing flow from input to consumer and name the observable change. A feature is not an implicit refactor or performance investigation. |
| [Laziness protocol](https://github.com/cursor/plugins/blob/aaeb0ea3a0584995aa8f55ce44c6c5259414b896/pstack/skills/principle-laziness-protocol/SKILL.md) | Prefer the smallest **readable, contract-preserving** change. Reuse the team's existing implementation rather than creating a wrapper or parallel path. |
| [Boundary discipline](https://github.com/cursor/plugins/blob/aaeb0ea3a0584995aa8f55ce44c6c5259414b896/pstack/skills/principle-boundary-discipline/SKILL.md) | Validate actual external inputs at their established boundary. Do not revalidate a guaranteed internal value or silently substitute a default for an unexpected failure. |
| [Prove it works](https://github.com/cursor/plugins/blob/aaeb0ea3a0584995aa8f55ce44c6c5259414b896/pstack/skills/principle-prove-it-works/SKILL.md) | Observe the changed behavior using an approved runner and fixture. A small diff is not proof of correctness; green tests are not proof that every edit was necessary. |

Do not run `poteto-mode` wholesale, launch competing implementations, strip comments, change models, or port autonomous review/merge routines. Select checks by failure risk, not a token percentage or check count. This setup must work regardless of the coding model.

## 2. Discover domain owners and propose the smallest harness change

1. Inspect each available repo **separately**: current entry points, accepted OpenSpec artifacts, applicable instructions, active specialists, orchestrator and reviewer. Confirm the actual Copilot session target and available delegation/review tools. A catalog entry is not an installed agent. If a repo, issue history, or capability is unavailable, mark it unverified; do not infer its conventions from the other repo.
2. For each bounded business process found, return one row: `repo | domain (trigger and exclusions) | owner: reuse/adapt/new | canonical flow + helper and caller (path:symbol) | local contract/exceptions | verification`. Use comparable current code and authorized issue/PR decisions; distinguish confirmed patterns from legacy workarounds. Do not create an agent for every language or directory. Reuse an owner across products only when its responsibility fits; its references and checks remain repo-specific.
3. Preserve mandatory specialist routing for **all dbt/Dagster mutations**, including shared helpers that affect the domain, one-line changes, renames and review corrections. Delegate before the first domain write; if the owner is missing, ambiguous or unavailable, stop that work. Split mixed tasks by ownership, with no overlapping writers. For other domains, propose equivalent routing where evidenced. Distinguish a routing instruction from an observed invocation and from a runtime-enforced restriction.
4. Propose exact harness-only edit paths: **one shared feature-change rule**, the smallest necessary local domain profiles/agents, the existing orchestrator's dispatch, and the existing reviewer's checklist. Reuse active files and reference the canonical rule; do not create a second OpenSpec process or a new reviewer for each product. Identify how each file is loaded, what already works, the pilot and rollback. If an equivalent rule already works, keep it. Ask for one bounded approval; then apply and verify only those changes. **Do not fix the historical feature in this setup run.**

## 3. Contract to install for future feature work

**Before editing:** name the approved behavior, its OpenSpec criterion (or quoted acceptance criterion), intended production paths, and relevant tests. Cite the existing helper/model/macro by path and symbol **and one current caller**; check whether its input, output, error behavior and layer fit. If none fits, say what was searched and why a new implementation is necessary. Do not introduce a cross-repo dependency merely because both products use the same technology.

**While editing:** preserve existing names, signatures, locations, formatting and unaffected consumers. No incidental renames or moves, cosmetic rewrites, whole-file formatting, unused compatibility wrappers, speculative fallbacks, or unmeasured optimizations. Keep required input validation, security, integrity and error visibility. If a refactor or wider change is genuinely necessary, show the blocked criterion and why a smaller valid alternative fails; obtain scope approval before proceeding. Mention optional improvements as follow-ups in chat, not extra files or edits in the MR.

**Test of necessity:** for each production hunk, complete *“Without this change, ___ fails”* with a specific acceptance criterion, existing contract, or mandatory repository invariant. If removing **your own** edit would preserve them all, leave it out. Do not physically revert someone else's changes to perform this reasoning. Two files changed in the correct layers are preferable to a shorter wrong-layer shortcut. Tests and test fixtures belong with the feature but are assessed separately from production churn; never cut tests, compress code, or delete useful comments to hit a line budget.

## 4. Pre-MR review: inspect without fixing

- Use the actual MR target (`main` if confirmed). Record target, merge-base and candidate IDs. For committed work, `git diff --find-renames <target>...HEAD` is the branch diff. Inspect staged, unstaged and intended untracked changes **separately** for a pre-commit candidate; do not confuse local-only work with the submitted MR. If the target/base is unavailable, request a local ref or MR diff, not credentials. Do not fetch, switch branches, stash, reset, or stage on the user's behalf.
- The reviewer reads the **actual diff**, not the implementer's summary. Separate production hunks, feature tests/fixtures, and other artifacts. Look inside approved files too: a valid feature edit can share a hunk with an unrelated rename. Check each production edit for necessity, domain placement, reuse and effects on existing callers. Identify pre-existing user work separately; flag unrelated content in the MR without rewriting it. A diff stat or rename detector can flag candidates, not decide intent.
- The implementer supplies verification tied to that candidate: behavior/assertion, approved command or UI action, expected vs observed result, exit status where applicable. Check the required feature, an affected existing consumer if shared code changed, and relevant architecture constraints. Use existing runners; prefer a precise dependency check over banning SQL constructs by regex. Missing evidence is **not verified**, not a pass. Repeat affected checks after a correction.
- Return a short read-only verdict: **PASS** = required behavior observed, domain routing evidenced where required, no unjustified production changes; **CHANGES NEEDED** = a demonstrated violation; **NOT VERIFIED** = missing base, ownership or required evidence. Report findings as `path:hunk/symbol | criterion or missing justification | evidence | smallest correction`. Group clean hunks; list only findings and material exceptions. Keep the reviewer read/search-only: supply the diff and check results, not write or shell tools. If independent review is unavailable, identify the human check still needed. The responsible specialist, not the reviewer, corrects its own work within scope.

## 5. Pilot and handoff

Use the selected incident to compare the old and new workflow with the same issue, repo snapshot, model and fixtures where feasible. Keep the rubric out of the test request. Use approved disposable fixtures, never a real deployment. Exercise at least these contrasts:

| Candidate | Expected result |
| --- | --- |
| Correct-layer change reusing a team helper, plus extensive relevant tests | Pass when behavior, routing and preserved contracts are demonstrated; the test volume is not noise. |
| Same green tests, plus an unrelated rename/move, formatter churn, duplicate helper or speculative fallback | Flag the specific unnecessary edit, even within an otherwise necessary file. Do not flag a documented input or integrity check as noise. |
| Smaller patch with identical rows but a transformation in the wrong layer, or protected edits with no specialist invocation | Reject the violated rule. Correct output, correct placement and correct routing are independent checks. |

In each available repo, verify that the orchestrator invokes the intended owner and that the owner cites **that repo's** helper/caller, conventions and checks. Return the approved files actually changed, domain map, pstack reuse mode (local source or embedded adaptation), baseline/candidate results, unverified items, and rollback limited to your changes. Measure unjustified production hunks and reviewer corrections separately from test changes; report time/cost only when observed. If you cannot run the pilot, give the exact manual probe and leave it pending. Do not claim that a Markdown rule alone enforces anything.
