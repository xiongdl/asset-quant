# Automation

This file defines when to reuse, change, or create project automation.
Project-specific commands and environments belong in `scripts/README.md`.

## Selection order

Keep a one-step system command inline. For repeated, multi-step,
project-specific, or error-prone work:

1. Search existing scripts, task runners, CI workflows, and documentation.
2. Reuse an entry point that already meets the need.
3. Extend an entry point only when the new behavior fits its current purpose
   and preserves its interface.
4. Otherwise, create one focused script under `scripts/`.

Role-policy automation is the exception: keep it under
`.agents/custom/scripts/`, invoke it only as documented by the applicable
policy file, and keep its interface documented there rather than in
`scripts/README.md`. It may use the host's standard-library-only `python3`
before the project environment exists when its policy file declares that
bootstrap dependency.

Do not add unrelated behavior to an existing entry point.

## Safety and documentation

- Preserve defaults and compatibility unless the approved task changes them.
- When compatibility must change, update affected callers, tests, and
  documentation in the same task.
- Do not commit credentials, local environments, or generated output unless
  the repository requires them.
- Keep temporary helpers outside the repository and remove them after use.
- Document every maintained script's inputs, options, prerequisites, outputs,
  and side effects in `scripts/README.md`.
