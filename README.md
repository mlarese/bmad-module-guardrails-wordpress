# Guardrails WordPress (`gwp`)

A focused BMad module for component-based WordPress architecture and controlled delivery through the release gate. It covers Gutenberg, Elementor, ACF, templates, the Media Library, and migration work.

This is a focused BMad module in the [Guardrails](https://github.com/mlarese/bmad-module-guardrails)
bundle. It keeps the same behavior and shared memory while installing only the figures and
workflows for the wordpress area.

> **Generated.** This repository is produced by `tools/build_modules.py` in the
> [bmad-module-guardrails](https://github.com/mlarese/bmad-module-guardrails) repository.
> Make changes there and regenerate; local changes here will be overwritten.

## Agents

| Agent | Role | Skill | Focus |
| ----- | ---- | ----- | ----- |
| 🧩 Milo | WordPress Component Architect | `grl-agent-wordpress` | Gutenberg, Elementor, ACF, post types, template parts, and the Media Library. |

## Skills and workflows

| Skill | Purpose |
| ----- | ------- |
| `gwp-profile` | Project profile | Collects the project context shared by every installed figure. |
| `gwp-board` | Multidisciplinary review | Convenes the relevant figures on one artifact and returns a review summary or release verdict. |
| `grl-wordpress-delivery` | Controlled WordPress delivery | Coordinates WordPress creation, migration, resumption, and verification through a release gate. |
| `grl-automation` | Controlled automation | Routes work from read-only checks through dry-run to observable execution, with explicit approvals and rollback. |

## Installation

```
bmad install gwp
```

As a first step, run `gwp-profile`. It collects the project profile — sector, data,
market, stack, and criticality — so each figure can calibrate its review. Without a profile,
the default remains `normal` and the figures start without context.

## Shared memory

The profile lives in `{project-root}/_bmad/memory/grl-shared/project-profile.md`, together
with `decisions.md` and `accepted-risks.md`. All Guardrails modules use the same path, so two
installed modules still share one profile.

## Using it with the bundle

This module installs skills with **the same names** as the `grl` bundle — `grl-agent-wordpress`
is identical in both. Do not install the full bundle and thematic modules in the same project:
choose the complete bundle, or only the thematic modules you need.

## License

MIT.
