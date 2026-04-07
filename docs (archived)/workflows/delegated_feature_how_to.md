# Delegated Feature How-To Protocol

## What This Is

When a feature is built by Codex or Claude (delegated), the developer does not own every line.
This protocol ensures that any delegated feature ships with a doc that gives full understanding
without requiring a line-by-line read. The doc lives in `docs/delegated/`.

The goal is not to document what the code does — it is to make the developer capable of:
- Running it without asking
- Modifying any part of it without asking
- Debugging a failure without asking

---

## When To Write It

Every time a full file or major feature is delegated. Write it **immediately after the code is created**, before moving on. If it was not written at creation time, write it on first touch.

---

## The Format

Every delegated doc follows this exact structure, in this order:

### 1. What It Is
One paragraph. Answer: what problem does this solve, why does it exist, where does it fit in the system.
No bullet lists. Write it like you are explaining to yourself 6 months from now.

### 2. The Whole Flow
A single ASCII diagram showing the entire file from entry point to output.
Every major step visible. Data transformations shown with arrows.
This is the map. The reader should be able to orient themselves anywhere in the code after reading this once.

### 3. Each Feature Flow
One section per major function or logical unit.
Each section has:
- An ASCII diagram showing that function's internal flow
- Inline explanation of non-obvious steps
- Any new Python pattern referenced explicitly (name + one-line explanation + why it's used here)

The flow must be detailed enough that the reader knows exactly what to change and where,
without a separate "modify points" list. If you read the flow and still don't know where to
make a change, the flow is not detailed enough.

### 4. How To Use
Exact commands only. No explanation. Copy-paste ready.
Cover: how to run it, common flags, where output lands.

---

## Rules

- Do not hold back. Write as much context as the feature needs.
- Reference any new Python pattern the first time it appears. Format:
  ```
  `pattern_name` — what it is in as many sentence as it takes for deep understanding. Why it's used here specifically.
  ```
- Never assume the reader will "figure it out from context."
- The flow diagrams are the primary teaching tool. Prose supports them, not the reverse.
- If the feature has external dependencies (env vars, other files it reads), list them explicitly.

---

## File Naming

```
docs/delegated/{feature_name}.md

Examples:
  docs/delegated/eval_run_eval.md
  docs/delegated/output_graph.md
  docs/delegated/orchestrator_graph.md
```
