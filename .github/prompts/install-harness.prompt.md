---
agent: 'agent'
description: 'Copy skills and their prompts from this harness repository into a work repository so Copilot can use them there.'
---

# Install the harness into a work repository

Target repository: ${input:target:Absolute path of the work repository, e.g. C:\repos\my-project}
Skills: ${input:skills:Skill folder names under skills\, comma separated, e.g. sql-server-lineage}

This workspace is the `agentic-harness` repository. Install the requested skills, and the prompts
that use them, into the target repository.

1. Check that the target path exists and is a git repository (it contains `.git`). If not, stop
   and say so.
2. For each skill, check that `skills\<skill>\SKILL.md` exists here. If not, stop and list the
   skills available under `skills\`.
3. Read the registry table in `prompts\README.md`. A prompt belongs to a skill when its *Uses*
   column names that skill. Collect those `*.prompt.md` files.
4. Before copying, list every file that already exists at its destination in the target. If any
   does, show the list and ask whether to overwrite; do not overwrite without an explicit yes.
5. Copy with one PowerShell command, asking for approval first:
   - `skills\<skill>\` to `<target>\.github\skills\<skill>\`, skipping `__pycache__`;
   - each collected prompt to `<target>\.github\prompts\`.
   Create `.github\skills` and `.github\prompts` in the target if they are missing.
6. Run `git -C <target> status --short` and show the result.

Rules:

- Write only inside `<target>\.github\skills\` and `<target>\.github\prompts\`.
- Do not commit, push or change anything else in the target repository.
- Do not copy third-party skills that are not in this repository.

Report:

- files copied, grouped by skill and prompts;
- the slash commands now available in the target (`/<prompt file name without .prompt.md>`),
  in the order listed in `prompts\README.md`;
- the next step: open the target repository in VS Code and run the first command.
