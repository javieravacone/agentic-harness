---
agent: 'agent'
description: 'Audit and implement domain-based delegation with distinct feature, refactoring and performance workflows in an existing Copilot harness.'
---

# Audit and implement domain owners and task workflows

Work inside Citrix, in ${input:repos:Authorized work repositories}. If pasted into chat, use the repositories named by the user. The **domain selects the subagent; the requested outcome selects its procedure**. Implement missing wiring, not a new agent for each combination. This is harness setup, not authorization to change product code.

## 1. Check what works today, without edits

Inspect each repository separately: active orchestrator, agent definitions, skills, scoped instructions, OpenSpec changes, canonical implementations and test runners. Check the selected Copilot runtime and any policy that affects delegation or skill loading. Do not infer activation from a filename or infer one repo's conventions from the other.

Return actual rows: `repo + bounded process | trigger/exclusions | current owner | procedure reachable for each intent | canonical helper/macro + one caller | verification | gap`. Cite paths, symbols and invocation evidence; mark unknowns. If a repo is inaccessible, name it. Reviewing an old patch is not a domain inventory.

## 2. Give each artifact one job

- **Orchestrator:** dispatch by affected behavior, passing the repo, issue/OpenSpec criterion, intent, allowed edits and invariants. Split genuinely mixed scopes or ask; never turn a feature into unsolicited cleanup or optimization.
- **Domain agent (`*.agent.md`):** own a bounded result. Define when it is called, what it can touch, allowed tools, stop conditions, and evidence it returns. Reuse a suitable owner; create one only for an evidenced responsibility. Delegate every dbt/Dagster mutation to its specialist **before the first write**, including tiny edits and corrections. If unavailable, stop that work unchanged.
- **Skill (`SKILL.md`) or existing playbook:** specify how to perform the selected procedure, its inputs and its proof of completion. Prefer one skill with three referenced playbooks if that fits; keep separate skills when independently reused. A skill does not grant tools or create a new actor.
- **Repository instructions/references:** keep stable local conventions, layer boundaries, approved commands and pointers to current examples here. `AGENTS.md` guides an agent; it does not define one. Reuse actual functions and macros from source, not Markdown copies. **OpenSpec/issue** holds this task's requested change, acceptance criteria and non-goals.

## 3. Wire these three procedures to the same owner

| Intent | Required procedure and evidence |
| --- | --- |
| Optimization | Agree on the metric and target. Measure a representative baseline, locate the bottleneck, then compare before/after under comparable conditions using the same fixture. Preserve output and contracts. No measurable baseline means no performance claim. |
| Refactoring | Name the structural change and pin current observable behavior before editing. Replay the same inputs before/after, including relevant errors or consumers. Require equivalence on the affected surface; compilation alone is insufficient. |
| Feature | State the new observable behavior, find a valid precedent and reuse the team's helper in the correct layer. Demonstrate the new case and an existing unaffected case. Make the smallest justified production diff; tests do not count as production noise. |

Reuse existing approved procedures; the table adapts [Poteto's playbooks](https://github.com/cursor/plugins/tree/aaeb0ea3a0584995aa8f55ce44c6c5259414b896/pstack/skills/poteto-mode/playbooks) and works without a plugin or external lookup. Do not add unrelated renames, moves, speculative fallbacks or formatting. If a skill has `disable-model-invocation: true`, do not assume automatic loading or silently change the flag. Distinguish a native skill invocation from reading a referenced playbook. Verify the chosen path or report the gap.

## 4. Apply the minimum change and prove it

Show `keep / adapt / create / blocked`, exact harness paths, expected before/after behavior and rollback. Wait for approval; then implement the approved delta. If it already works, change nothing. Preserve user work. Keep private evidence local. Each terminal command requires separate approval. Do not install anything, weaken permissions, enable hooks, touch production, commit or push.

In approved disposable fixtures, give the orchestrator three natural requests about **the same component** in fresh sessions: make it faster; change its structure without changing behavior; add one capability. Do not name the expected agent or skill. Verify each available repo's routing at least once. Report `request | actual owner and invocation | actual procedure used | repo-specific reference | expected vs observed result | PASS / FAIL / NOT VERIFIED`. Include command or UI evidence and exit status where applicable. A listed file, reviewer opinion or self-report is not proof. Distinguish observed routing from enforced routing. Finish with files actually changed, effective impact and any precise remaining manual check.
