# ADX Harness

This repository is a Claude Code plugin. Keep it small, inspectable, and useful
outside software development.

## Product principles

- Keep always-loaded instructions short. Put domain detail in skills and references.
- Prefer one deterministic runtime over overlapping commands and services.
- Usability first: the harness must work through lifecycle hooks without the user
  running anything. Every command is optional maintenance, not part of daily use.
- Ask only when ambiguity materially changes the outcome. Otherwise state the assumption and proceed.
- Make the minimum change that satisfies the request. Do not add speculative flexibility.
- Define a verifiable result for non-trivial work and check it before finishing.
- Preserve raw turn history locally; promote only validated, durable knowledge to the project wiki.
- Never archive secrets, credentials, raw tool output, or hidden model reasoning.

## Structure

Installing a plugin copies its source directory verbatim, with no ignore list.
So `plugin/` holds everything that ships, and project state, evidence, and the
development harness stay outside it.

- `plugin/.claude-plugin/plugin.json`: plugin metadata
- `plugin/agents/`: the default personal copilot and bounded subagents
- `plugin/skills/`: conditional marketing, writing, design, and knowledge guidance
- `plugin/commands/`: optional slash commands (`status`, `summary`, `check`)
- `plugin/hooks/hooks.json`: lifecycle wiring
- `plugin/scripts/harness.py`: lifecycle orchestration, turn archiving, digests
- `plugin/scripts/knowledge.py`: disposable SQLite FTS index over Markdown knowledge
- `plugin/scripts/skill_router.py`: precision-first per-prompt skill suggestions
- `plugin/scripts/eval_routing.py`: scored real-usage routing evaluation
- `plugin/config/skill-routing.json`: deterministic routing policy
- `plugin/templates/`: global and project-local knowledge templates
- `.claude-plugin/marketplace.json`: local marketplace so the plugin can be installed
- `harness`: root shim so maintenance is one short command
- `evals/real-usage/`: labeled routing scenarios and the execution rubric
- `tests/`: deterministic runtime tests
- `.harness/`: this repository's own project state — never packaged

## Verification

```bash
python3 -m unittest discover -s tests -v
python3 plugin/scripts/eval_routing.py
./harness status
claude plugin validate plugin/.claude-plugin/plugin.json --strict
claude plugin validate . --strict
```

`./harness status` already runs doctor, the routing evaluation, the knowledge
index check, and today's digest. `validate .` checks the marketplace manifest, so
the plugin manifest needs its own path.

Keep Python runtime code standard-library only.
