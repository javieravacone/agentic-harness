---
agent: 'agent'
description: 'One sentence: what this prompt produces and when to use it.'
---

# <Prompt title>

<!-- Problem: As a <role>, when <situation>, I lose or risk <cost>. Symptom: <fact>. -->

Input: ${input:name:What to provide, with an example}

Steps:

1. <What to read first.>
2. <What to produce.>

Rules:

- Cite `path:line` for every claim about the code.
- <What the model must not do: edit, run, guess.>

Report:

- <What the answer must contain.>
- Open questions, each with its evidence.
