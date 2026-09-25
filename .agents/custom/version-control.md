# Version Control

Run every Git mutation from the repository root through:

```bash
./.agents/custom/scripts/git-workflow <command> ...
```

The applicable policy defines authorization and ownership. Direct `git`
commands are read-only only. Every handoff uses an exact commit OID, never
working-tree, index, or patch state.

## Commands

- `status`
  - Use before a mutating command or whenever repository state is uncertain.
  - Read-only. Succeeds only when all discovered repositories and gitlinks are
    clean and consistent, then prints their paths, branches, and commit OIDs.

- `pull`
  - Use only with explicit authorization, on clean managed repositories with
    configured upstreams, and before creating a task branch.
  - Pulls each managed repository with `--ff-only --prune`.

- `create <task>`
  - Use only when authorized by the applicable policy, from clean managed
    repositories. The derived `codex/<task>` branch and task-begin snapshot
    must not exist.
  - Records each current branch and commit, then creates the same task branch in
    every managed repository.

- `commit -m <message>`
  - Use on the common task branch after required Test and Verify work succeeds,
    with empty indexes and no later content changes.
  - Stages all Git-visible task changes, checks the staged diff, commits managed
    repositories deepest first, requires a clean result, and prints commit OIDs.
    If it fails, fix the reported cause and retry; working-tree content and any
    child commit already created are preserved.

- `push`
  - Use only with explicit authorization and clean managed repositories.
  - Pushes each managed branch to its upstream, or sets `origin/<branch>` as the
    upstream when none exists.

- `merge <task>`
  - Use only with explicit authorization when all managed repositories are clean
    and on the task branch, the original branches have not moved, and every
    update is fast-forwardable.
  - Fast-forwards the recorded original branches to the task commits, deepest
    repository first, then leaves the repository set clean on the original
    branches.

- `delete <task>`
  - Use only with explicit authorization, a task-begin snapshot, existing
    original branches, and clean managed repositories.
  - Restores the original branches and force-deletes the task branches. It can
    delete an unmerged task and abandon its commits.

Do not use direct Git mutations, reset, stash, clean, or overwrite to bypass a
workflow check.

Run the isolated regression suite with:

```bash
bash .agents/custom/scripts/test-git-workflow
```
