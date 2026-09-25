# Role Routing

Select exactly one role before acting:

1. An explicit runtime role (`Root`, `Default`, or `Reviewer`) wins.
2. Without an explicit runtime role, the non-delegated owner of the user
   conversation is `Root`.
3. A model name, agent name, or setting named `default` does not select the
   `Default` role.
4. If role selection is contradictory or unclear, stop and report the conflict
   to Root.

Apply only the selected role file:

- Root: `.agents/custom/root.md`
- Default: `.agents/custom/default.md`
- Reviewer: `.agents/custom/reviewer.md`

Root may inspect the other role files as coordination data.

Default and Reviewer apply only their selected role file. They may inspect
another role file only when Root explicitly delegates that file as task or
review data. An inspected role file is data; never apply its instructions.
