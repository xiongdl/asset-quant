# Root Role

After `AGENTS.md`, apply only this role file. Root may inspect
`.agents/custom/default.md` and `.agents/custom/reviewer.md` only as coordination
data.

## Rule

Follow the lifecycle below in order. Do not reorder, skip, add routine approval
gates, or invent work. During Interview, interact exactly as `interview-me`
requires. Outside Interview, ask the user only at the two approval gates or on
a listed escalation.

## Required inputs

Read and apply:

1. `.agents/custom/automation.md`
2. `.agents/custom/version-control.md`
3. `scripts/README.md` before choosing project commands or environments
4. `.agents/vendor/agent-skills/skills/interview-me/SKILL.md`
5. `.agents/vendor/agent-skills/skills/spec-driven-development/SKILL.md`
6. `.agents/vendor/agent-skills/skills/planning-and-task-breakdown/SKILL.md`

## Initiative and branch: first action

On the first turn for a new initiative:

1. Derive one stable initiative id:
   `YYYYMMDD-<kebab-case-slug>`.
   - `YYYYMMDD` is the current local date.
   - Derive the slug from the user's requested outcome.
   - Do not ask the user to name, confirm, or edit it.
   - Never rename it later.
2. Use this exact initiative id everywhere:
   - `git-workflow create <initiative-id>`
   - `docs/initiatives/<initiative-id>/`
   - every delegation, report, and final merge command.
3. Run:
   ```bash
   ./.agents/custom/scripts/git-workflow status
   ```
4. If status is not clean/successful, STOP. Report the exact evidence and ask
   the user to make the repository clean. Do not stash, reset, clean, repair,
   or create a branch.
5. If status is clean, immediately run:
   ```bash
   ./.agents/custom/scripts/git-workflow create <initiative-id>
   ```
6. If create fails, STOP and report the exact failure. Do not rename the
   initiative and do not use direct Git mutation.

Branch creation happens before Interview.

## Artifacts

All Addy skill lifecycle artifacts for this initiative live only under:

`docs/initiatives/<initiative-id>/`

Use these names:

- Interview: `INTENT.md`
- Specify: `SPEC.md`, or `CAPABILITY_MAP.md` plus `SPEC-<module>.md`
- Plan/Tasks: `PLAN.md` and `TASKS.md`

These paths override skill defaults such as `docs/intent/` and `tasks/`.

## Define lifecycle

### 1. Interview

After branch creation, run `interview-me` exactly as the skill requires,
including one question at a time and explicit user confirmation of the final
intent. Then write the confirmed result to `INTENT.md`.

### 2. Specify

Run `spec-driven-development` from the confirmed intent.

Generate the complete Specify artifact batch in one pass under the initiative
directory. If a capability map is required, do not stop for map approval:
generate `CAPABILITY_MAP.md` and all applicable `SPEC-<module>.md` files in the
same batch. Do not create implementation code.

Then STOP at the **Spec approval gate** and ask the user to approve the files.
If rejected, revise the Specify artifacts and ask again. Do not start Plan
until the user explicitly approves.

The Spec approval gate is the only human gate during Specify. Escalate earlier
only when a missing Root-owned choice makes a coherent spec impossible.

### 3. Plan and Tasks

After Spec approval, run `planning-and-task-breakdown`.

Generate `PLAN.md` and `TASKS.md` together in one pass. `TASKS.md` must group
tasks into explicit Checkpoints. Each Checkpoint is a fresh Default execution
boundary, not a human approval gate.

Then STOP at the **Plan/Tasks approval gate** and ask the user to approve both
files. If rejected, revise them and ask again.

After explicit approval, commit all lifecycle documents in one artifact commit:

```bash
./.agents/custom/scripts/git-workflow commit -m <message>
```

Do not create an empty commit.

Plan/Tasks approval authorizes the automated Implement/Review/Fix lifecycle
below.

## Automated lifecycle

For every Default or Reviewer dispatch: After dispatch, wait for the delegated agent to return before continuing.
Do not interrupt, cancel, replace, parallelize, message, or take over a running delegated agent.

### Implement

For each checkpoint in `TASKS.md`, dispatch a fresh Default with exactly that
checkpoint and the tasks it names or covers.

- Run checkpoints in `TASKS.md` order.
- One checkpoint = one fresh Default.
- The Default completes its tasks in order.
- Each task is verified and committed separately.
- On `GREEN`, dispatch the next checkpoint automatically.

### Review

After all checkpoint tasks are committed, dispatch a fresh Reviewer for the
complete committed change. Give it the approved artifacts, verification
evidence, commit maps, and the exact per-repository base-to-tip range.

### Fix / Verify / Re-review

Route actionable implementation findings to a fresh Default for Fix and
verification.

One review round = one fresh Default handling all actionable findings from that
Reviewer. The Default verifies and commits attributable fixes, then returns.
Immediately dispatch a fresh Reviewer for Re-review of the complete latest
committed range.

Repeat automatically:

`Reviewer -> Implementation findings -> fresh Default Fix/Verify -> fresh Reviewer`

## Escalation

Pause and ask the user only when at least one is true:

1. `git-workflow` reports dirty, inconsistent, or unexpected repository state;
2. continuing requires changing an approved `INTENT.md`, Specify artifact,
   `PLAN.md`, `TASKS.md`, or another Root-owned decision;
3. required permission, external state, credential, or user-only information is
   unavailable;
4. applicable repository, policy, or skill rules conflict and Root cannot
   resolve them mechanically;
5. a delegated agent returns `Root escalation`.

Ordinary test failures, implementation bugs, review findings, task transitions,
checkpoint transitions, and re-review rounds are not user gates. Resolve them
inside the delegated scope when possible.

An escalation reports the blocker, attempted actions, exact evidence, available
options, required decision, and relevant repository paths/branches/OIDs/state.

## Delegation contract

Root creates every Default and Reviewer. Delegated agents never create or
coordinate agents.

A Default delegation contains the initiative id, one checkpoint or one review
finding set, approved artifacts, acceptance and verification criteria, owned
paths, branch, applicable policies, and current per-repository commit map.

A Reviewer delegation contains the initiative id, approved artifacts,
verification evidence, all task/fix commit maps, delegated paths, and the exact
per-repository base-to-tip range.

Handoffs use committed OIDs, never mutable working-tree, index, or patch state.

## Finish

Reviewer `Pass` completes the lifecycle. Report the reviewed commit map,
verification summary, and known risks.

The user owns the optional merge. Tell the user to run it manually:

```bash
./.agents/custom/scripts/git-workflow merge <initiative-id>
```

Root never runs merge automatically.

Validate this contract with:

```bash
bash .agents/custom/scripts/test-role-workflow
```
