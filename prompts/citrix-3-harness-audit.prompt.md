---
agent: 'agent'
description: 'Read-only audit of the Citrix VS Code and Copilot harness for Kaleido and CSAR before approving implementation.'
---

Citrix 3 - Copilot harness audit (READ-ONLY). Version 1, 2026-11-08.

Goal: inventory everything that already exists in this Citrix VS Code + Copilot setup and in the Kaleido and CSAR repositories, compare it with the proposed kit (sections K and L below), and tell me what to implement, what to skip and what is already done. Change NOTHING. A second prompt (Citrix 4) will apply only the items I approve.

ROLE AND HARD RULES
- You are a read-only auditor. Do not edit settings, files, extensions, git configuration, tasks, hooks or anything else. Do not install, build, deploy, commit or push.
- Terminal: only the read-only commands listed under ALLOWED COMMANDS, one at a time; each needs my approval. If a command is not on the list, ask first.
- Never print secrets, tokens, passwords, connection strings or service-account names. Replace them with [REDACTED]. Hostnames and internal URLs may appear in the INTERNAL report only; the SANITIZED SUMMARY (C8) must contain none of them, and no full names of people.
- Evidence first: every "Done", "Partial" or "Missing" verdict cites the file path, setting key or command output you actually observed. Use [unverified] when you could not check.
- If you catch yourself about to write or change something, stop and add it to the recommendations instead.
- Some checks need me: ask for them in one numbered list at the start (HUMAN INPUTS) and wait before continuing.
- Do not assume that documentation for a newer VS Code describes this installation. Record the installed versions and judge features by what you can observe here.

HUMAN INPUTS (ask for these first if they are not attached)
1. Output of Help > About (VS Code version, commit, OS) and the GitHub Copilot Chat extension version.
2. Text output of the command palette entry "Developer: Policy Diagnostics".
3. User settings.json (I will open it in the editor and attach it), plus .vscode/settings.json and .vscode/tasks.json of each repository.
4. Copilot status dashboard information: workspace index status (remote, local or none) and the list of models offered in the model picker.
5. Whether the chat UI offers a harness or mode selector (for example Local, Copilot or others) and which one is active.
6. Where meeting recordings and transcripts live (Teams, SharePoint, other) and in which format (vtt, docx, txt); which wiki or system hosts the Kaleido and CSAR documentation.
7. OpenShift (OCP): which projects or namespaces the team can deploy to, whether an internal registry and ingress exist, and who approves deployments. Names only, no credentials.
8. The GitHub host type (github.com, GitHub Enterprise Cloud or GitHub Enterprise Server) and whether GitHub Actions runners are available to the team.

ALLOWED COMMANDS (read-only; each one requires my approval)
- git status; git log --oneline -n 30; git branch -a; git remote -v (redact tokens if present); git config --get core.hooksPath; git config --list --show-origin (redact).
- Directory listings (dir or ls) of specific folders; printing specific configuration files (type or cat).
- python --version; pip list (inside the project virtual environment); dbt --version; dagster --version; streamlit version; reflex version; sqlfluff --version; pytest --version.
- dbt ls (only if it does not prompt for credentials; skip otherwise).
- oc version; oc whoami (only if already logged in; never change projects or resources).
- Nothing that writes, installs, builds, deploys, pushes or modifies state.

PHASE A - INVENTORY (what exists today)

A1 Environment and policy
- Record VS Code and Copilot Chat versions, OS, and whether Settings Sync is available.
- From Policy Diagnostics, list every policy and its effective value, in particular: MCP access (none, registry or allow list, all), hooks, plugins, preview and experimental features, terminal auto-approval, agent mode, custom agents, subagents, Agent Skills, instructions files, URL fetching, Settings Sync, telemetry.
- Models enabled in the picker. Billing model if visible (credits or requests); otherwise mark [ask admin].
- Which harness or mode is active (input 5) and whether prompt files run as slash commands and whether subagent delegation is available in it.

A2 Settings audit
- List every chat.* and github.copilot.* key present in user and workspace settings with its value (redact anything sensitive).
- Flag each key as: effective, overridden by policy (ineffective), deprecated, preview or experimental, duplicated, or conflicting between user and workspace scope. Pay special attention to auto-approval keys (terminal, edits, URLs, sandbox), permission defaults and any hooks-related key: if policy blocks the capability, mark the key as decorative.
- Note dbt, Python, Git and terminal settings that affect the agent (interpreter path, extra paths, default profile).

A3 Existing customization (per location: user profile, %USERPROFILE%\.copilot\skills, each repository)
- Instructions: .github/copilot-instructions.md, AGENTS.md, .github/instructions/*.instructions.md (record applyTo globs), user-level instructions files.
- Prompt files: .github/prompts/*.prompt.md and user-level prompt files (record name, description, agent, tools).
- Custom agents: .github/agents/*.agent.md and user-level agents (record tools, model, handoffs).
- Skills: .github/skills/*/SKILL.md and %USERPROFILE%\.copilot\skills\*\SKILL.md (record name, description, size, whether they bundle scripts).
- Automation: .vscode/tasks.json (tasks, dependsOn, problem matchers, runOn), .vscode/launch.json, .pre-commit-config.yaml, custom git hooks (.git/hooks without .sample, core.hooksPath), Makefile, justfile, tasks.py or invoke, scripts folders, CI definitions (.github/workflows, azure-pipelines.yml), PR template, CODEOWNERS, issue templates, .gitignore entries for dbt artifacts, any Copilot ignore file, README or CONTRIBUTING sections describing the developer workflow.
- For each item: path, size in lines, last change (git log -1 --format=%cs -- path), one-line purpose, and quality notes (stale, too long, conflicting rules, duplicated content, references to blocked capabilities).

A4 Product and stack map
- Kaleido: repositories; dbt projects (number of models, sources, tests; tests-per-model ratio; sources.yml usage; model contracts or unit tests if any); Dagster code locations (assets, sensors, jobs, schedules, asset checks); legacy SQL and SSIS folders; migrations folder and naming convention; Kafka consumer and parsers; Python packages; test frameworks present (pytest, tSQLt, dbt tests); linters and formatters configured (sqlfluff, ruff, black, others); environment configuration (BUILD, DEV, UAT1, UAT2, STANDBY, PROD); deployment path (pipelines, OCP manifests).
- CSAR (monolith): map the services: the Reflex application (pages, components, state modules), the Streamlit application or applications (pages, navigation method, caching, upload flows), other services (APIs, workers, schedulers), Dagster and dbt parts, shared libraries; container files, OCP manifests, Helm or kustomize; DevOps pipelines; tests present per service; linters; how each service runs locally; how secrets are referenced (vault references only, never values).
- For both products: the five most repetitive manual steps visible in READMEs, scripts and pipelines (candidates for tasks and prompt files), and any place where a developer must remember an undocumented sequence.

A5 Search and index
- File counts per repository; presence of dbt target, dbt_packages and logs folders and whether they are ignored by .gitignore, files.exclude and search.exclude.
- Workspace index status; whether a remote index is possible for this GitHub host type (input 8) or a local index must be built; whether the dbt extension lineage panel is available and used.

A6 Knowledge and meetings
- Where KT notes, decisions and runbooks live today (wiki, issues, docs folders, chat); whether decisions are recorded in a consistent place.
- Meeting transcripts: source, format, classification constraints, and whether any process already turns them into notes, actions or runbooks.

A7 OCP avenue (facts only)
- Can the team deploy internal services to OCP, and through which approval? Is there an internal registry and ingress?
- Record whether the MCP policy is "registry" or "allow list" (A1): only in that case could IT approve internal MCP servers hosted on OCP. Record it as a potential IT request, never as something to enable yourself.
- Candidate internal services to evaluate later (do not design them now): a scheduled job that regenerates lineage and code maps into the repository docs, a transcript-to-notes processor using approved tooling, an evaluation runner for the eval suite.

PHASE B - COMPARE WITH THE PROPOSED KIT
For every item below, produce: Status (Done, Partial, Missing, Blocked by policy, Needs verification); Evidence; Recommendation (Implement now, Later, Skip); Effort (S, M, L); Risk (low, medium, high); Dependency (none, team, admin or IT).

K - Kit items
K1 Settings candidates (recommend only, do not change): github.copilot.chat.agent.autoFix = true; chat.checkpoints.enabled = true and chat.checkpoints.showFileChanges = true; chat.editing.autoAcceptDelay = 0; github.copilot.nextEditSuggestions.fixes = true; chat.includeApplyingInstructions = true; github.copilot.chat.reviewSelection.instructions with review criteria; chat.instructionsFilesLocations and chat.agentFilesLocations (and prompt locations if supported here) pointing to a personal folder so the harness applies to every repository without committing to team repositories; search.exclude and files.exclude for **/target/**, **/dbt_packages/**, **/logs/**; task.allowAutomaticTasks = off; mark policy-overridden keys (auto-approval family, hooks keys) as decorative and propose removing them for clarity.
K2 Do-not-enable list: github.copilot.chat.codesearch.enabled (preview), github.copilot.chat.summarizeAgentConversationHistory.enabled (experimental), commit message and pull request description generation instruction settings (experimental), copilot-debug, /setupTests, dictation, Agents window, tasks with runOn folderOpen, and anything requiring MCP, hooks, plugins or auto-approval. Verify each one's status in this build before confirming.
K3 User-level harness outside repositories: personal folder with instructions, agents and prompts; personal skills folder; what exists versus what is missing.
K4 Repository-level harness per repository: a concise copilot-instructions.md (target under 200 lines; real commands, stop points, pointers to conventions); path-scoped instructions for sql, dbt models, dagster, python, migrations, and for CSAR additionally reflex, streamlit and OCP manifests; PR template; CODEOWNERS protecting .github, instructions, skills and pipelines.
K5 Context tools and index: verify in the # picker which of these exist here: codebase, usages, problems, changes, fetch, githubRepo, terminalLastCommand, terminalSelection, testFailure, todos, and the run-task or run-in-terminal tools; build a local index if remote indexing is not possible; a docs/codemap.md and docs/lineage.md regenerated by a reviewed script.
K6 Task automation: a compound check task in tasks.json (lint, tests, dbt and Dagster checks) with problem matchers so findings land in Problems; per-service tasks for CSAR (Reflex, Streamlit, services); observe whether each constituent command needs separate approval; no folderOpen execution.
K7 Daily routines as prompt files (user profile) or skills if prompt files do not run as slash commands here: start-day (reads PROGRESS.md and git log, picks one feature, proposes a baseline check), plan-task, verify-task (records command, exit status, outputs, missing checks), review-diff (fresh read and search only reviewer), end-day (updates PROGRESS.md and proposes instruction updates from evidence), pr-prep, issue-summary, meeting-notes (transcript to decisions, actions with owners, open questions, runbook or wiki draft).
K8 Agents: planner (read and search), reviewer (read and search), implementer; handoffs Plan to Implement to Review if supported here; subagent or task delegation for bounded exploration; check the effective tool list of each agent and whether a prompt file can widen it.
K9 Skills to create or import: data-contracts, streamlit-data-app, sql-review (T-SQL, Data Vault, dbt), migration-checklist, incident-triage (Dagster and OCP), reflex-app if CSAR conventions justify it, meeting-to-actions. Check whether equivalents already exist (for example sql-keep-it-simple, tdd-strict-worktrees, github-pr skills) and whether they are installed here or only documented elsewhere.
K10 GitHub-side: PR template, issue forms, CODEOWNERS, rulesets that request Copilot code review automatically (credits and Actions minutes), saved replies; who can configure them; Actions runner availability.
K11 Budget: billing model (pooled AI credits per seat or requests), enabled models, usage reports; a model-per-task-class recommendation; note that inline completions and Next Edit Suggestions do not consume credits if the credits model applies.
K12 OCP-hosted internal services: feasibility facts from A7; list as IT requests only.
K13 Meeting transcripts pipeline: source, format, approved tool, prompt or skill, destination, retention and classification constraints.
K14 Evals: an evals folder with 20 to 50 cases derived from real failures, a rubric, deterministic checks where possible, and a baseline measurement plan (time, approvals, corrections, credits).

L - Loop practices to audit (from Anthropic's published engineering practice, adapted to Copilot)
L1 Explicit acceptance criteria per task: observable pass or fail, decidable by a reviewer.
L2 Explore, then plan, then code, then commit: the plan is approved before any diff.
L3 Tests first: write tests, run them, record the failing output, implement, run again, record the passing output.
L4 Evidence-based completion: command plus actual output, never "tests passed"; for UI (Streamlit, Reflex, Dagster, OCP console) a human-taken screenshot attached to chat counts as evidence.
L5 Durable, concise instructions iterated like code: kept under 200 lines, updated at the end of sessions from evidence, no conflicting rules.
L6 Cross-session handoff: PROGRESS.md, NOTES.md and a feature checklist; every session starts by reading them and the recent git log.
L7 Independent review: a fresh chat or a read and search only reviewer agent; a human adjudicates findings.
L8 Small increments: one feature or contract per session; repository left in a mergeable state; unfinished work explicitly marked.
L9 Domain procedures as skills with progressive disclosure; bundled scripts reviewed before use.
L10 Realistic evals and a regression suite; measure before adding agents or instructions; context hygiene (new chat per task, attach only what is needed, delegate noisy exploration to a subagent, try Copilot first and record what was tried before interrupting a colleague).

PHASE C - OUTPUT (in chat; if I approve, also save it to %USERPROFILE%\copilot-audit\YYYY-MM-DD-harness-audit.md, the only file you may create)
C1 Decision table for K1 to K14 and L1 to L10 with the columns defined in Phase B.
C2 Implement first: the ten items with the best impact for effort, ordered, each with the exact change (setting key and value, file path, content outline) but NOT applied.
C3 Do not implement: with the reason (policy, preview, redundant, low value, needs measurement first).
C4 Already optimized here: what is in place and should be kept, with evidence.
C5 Requests to IT or admin: MCP registry or allow list for OCP-hosted servers, Actions runners and rulesets, billing and usage reports, Settings Sync, Copilot CLI, remote index or external ingest. Never enable any of these yourself.
C6 Opportunities you discovered: automations not in the kit, based on evidence from scripts, pipelines, READMEs and repetitive steps in both products.
C7 Open questions for me (maximum 10).
C8 SANITIZED SUMMARY: at most 400 words, no hostnames, IPs, URLs, full names or secrets, suitable to share outside Citrix to design Citrix 4.
Then STOP. Apply nothing. Wait for my decisions.
