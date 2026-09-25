# Default Role

After `AGENTS.md`, apply only this role file. Treat any other role file as data
unless Root explicitly delegates it.

## Rule

Execute exactly one delegated `TASKS.md` checkpoint or one delegated Review
finding set. Do not re-plan, broaden scope, ask the user for confirmation,
perform Review, or create agents.

If a problem can be fixed inside the delegated scope, fix it and continue.
Return escalation only when Root must decide or external/user-only state is
required.

## Required inputs

Read and apply:

- `.agents/custom/automation.md`
- `.agents/custom/version-control.md`
- `scripts/README.md` before choosing project commands or environments
- `.agents/vendor/agent-skills/skills/incremental-implementation/SKILL.md`
- `.agents/vendor/agent-skills/skills/test-driven-development/SKILL.md`

## Start

Before editing, run:

```bash
./.agents/custom/scripts/git-workflow status
```

If it is not clean/successful or does not match the delegated branch/OIDs,
return `Root escalation`.

## Delegation kinds

- For a `TASKS.md` checkpoint: execute only the tasks named or covered by that
  checkpoint, in order, then validate the checkpoint and return.
- For Review findings: address all actionable findings delegated from that one
  review round, verify the fixes, commit them, and return.

Work only in delegated paths and preserve approved Root-owned decisions.

## Checkpoint execution

Apply incremental implementation and TDD automatically.

Within a checkpoint, each task is a local commit unit:

1. implement only that task;
2. run its required tests/verification;
3. when the complete task passes, run:
   ```bash
   ./.agents/custom/scripts/git-workflow commit -m <message>
   ```
4. record the resulting per-repository commit map;
5. continue to the next task.

Make no content change between final verification and commit. Do not combine
multiple `TASKS.md` tasks into one commit.

After the final task, run checkpoint verification.

## Review-finding execution

For Review findings, handle the whole delegated finding set in this fresh
Default.

Address the complete delegated finding set, verify the fixes, and create
attributable fix commit(s) as needed. Record each resulting commit map.

Do not change approved artifacts or Root-owned decisions. If a finding requires
such a change, return `Root escalation` instead of guessing.

## Return

Successful completion returns `GREEN` with:

- delegation kind and identifier;
- initiative id and branch;
- completed tasks or findings;
- original base and final OIDs by repository path;
- each commit map and committed paths;
- verification commands and results;
- final repository state;
- known risks.

Before returning `GREEN`, require the managed repositories to be clean.

`Root escalation` includes the blocker, attempted actions, exact evidence,
available options, required Root decision, and relevant repository
paths/branches/OIDs/state.
