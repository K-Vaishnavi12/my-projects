# AI-Assisted Development Workflow

The syllabus's "AI Assisted Development" module asks you to describe
how tools like Copilot, Cursor, or Claude Code were used in the
project. Here's an honest account for **Symposium**.

## Tools in the loop

| Tool | Role |
|---|---|
| **OpenCode CLI** (Claude Opus 4.7) | Primary agent — scaffolded the entire project, generated ETL/ML/agent code, wrote SQL DDL, produced docs. |
| **GitHub Copilot** (VS Code) | Inline completions during manual edits — mostly test cases and small refactors. |
| **Google Gemini 2.0 Flash** | The *product's* LLM (not a dev tool) — powers the persona agents and moderator. |

## Workflow

1. **Design phase**
   - Talked through architecture with the agent using bulleted
     requirements and syllabus topics as a checklist.
   - Committed to a star schema and multi-agent design *before* any
     code was written. This kept the AI focused instead of jumping
     between styles.

2. **Scaffolding phase**
   - Asked the agent to generate the folder tree first, then create
     empty modules with docstrings only.
   - Reviewed and adjusted the folder names before letting it fill in
     implementations — cheap to change directions early.

3. **Implementation phase**
   - Fed the agent one module at a time (e.g. "write the SVM stance
     classifier following the interface used by the other ML modules").
   - Used the docstring convention as the *specification* — every
     model exposes the same `train / predict / save / load` shape.

4. **Prompt engineering as code**
   - System prompts + few-shots for the personas live in
     `symposium/config/personas.py` (data), not scattered through
     agent code.
   - Anti-hallucination guardrails live in
     `symposium/prompts/templates.py` (source-of-truth).
   - This makes prompts diff-able, reviewable in PRs, and testable.

5. **Testing phase**
   - Asked the agent for unit tests of pure functions (cleaner,
     chunker, persona classifier).
   - Manually wrote integration tests for the SQL layer.

## What worked

- **Type hints + pydantic settings** as the API contract. Every AI
  suggestion is easy to reject when the shape is wrong.
- **Small, docstring-driven modules**. Each file is under 300 lines;
  the agent doesn't need the whole codebase in context.
- **Named prompts**. Storing prompt strings in `symposium/prompts/`
  as constants (not f-strings scattered in agent code) made
  prompt-tuning trivial.

## What didn't

- Trusting AI-generated SQL joins without running them. Always ran
  the file against a live SQLite db before committing.
- Auto-generated tests were often too shallow — usually verified
  return types but not values. Kept them but added assertive tests
  manually.

## Lessons for the SME connect

- Treat the AI as a *pair programmer with amnesia*: it doesn't
  remember what it wrote yesterday. Feed it the interface, not the
  history.
- Version-control prompts the same way you version-control code. A
  git diff on a prompt is more valuable than one on the response.
- Use decorators + guardrails to *automate* what you'd otherwise ask
  the AI to remember (retries, logging, safety rules).
