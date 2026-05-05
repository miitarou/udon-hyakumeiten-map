# Claude Code Project Rules

## Language

- Explain work in Japanese.
- Write code, identifiers, commands, and commit messages in the language already used by the project unless asked otherwise.

## Safety

- Before changing files, state the intended scope and the files likely to change.
- Do not delete, overwrite, reset, clean, or rename files without explicit confirmation.
- Do not modify production credentials, deployment settings, or secret files automatically.
- Do not read `.env`, `.env.*`, `secrets/`, SSH keys, or cloud credentials unless the user explicitly asks and explains the purpose.

## Coding Style

- Follow the existing project conventions.
- Prefer minimal, targeted changes.
- Avoid broad refactors unless the user asks for them.
- Preserve unrelated user changes in the working tree.

## Execution Policy

- Inspect the current state before making assumptions.
- Show or summarize important diffs before risky changes.
- Run focused verification after edits when practical.
- Do not auto-stage, auto-commit, or push unless explicitly requested.
