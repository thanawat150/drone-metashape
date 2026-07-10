You are setting up repository-level Codex governance for:

`thanawat150/drone-metashape`

This task is only about repository instructions, reusable skills, scoped agent rules, and development workflow.

Do not implement Phase 4.5, Phase 5, or modify the Metashape processing behavior in this task.

# Objective

Make this repository easy and safe to work with through Codex by establishing:

1. A root `AGENTS.md` as the canonical repository instruction file.
2. Reusable `SKILL.md` files for major task types.
3. Scoped `AGENTS.md` files for the pipeline, web UI, and tests.
4. Clear rules for selecting the correct Skill.
5. A lightweight issue → branch → implementation → test → PR workflow.
6. Explicit safety rules for generated drone data, Metashape outputs, secrets, and production processing.
7. Documentation explaining how humans and Codex should use the system.

Normal users running the Orthomosaic application must not require Codex or any AI service.

---

# Existing repository context

The repository currently contains:

* root `SKILLS.md`;
* `skills/drone-metashape-local-one-click/SKILL.md`;
* `metashape_pipeline/`;
* `web/`;
* `tests/`;
* `work/` legacy scripts;
* `app.py`;
* `start.bat`;
* mock-mode tests;
* Phase 0–4 implementation;
* documentation under `docs/`.

The existing skill and documentation must be inspected before changes are made.

Do not assume the repository exactly matches this description. Verify the actual tree first.

---

# Mandatory inspection

Before editing:

1. Inspect the repository tree.
2. Read:

   * root `SKILLS.md`;
   * existing `skills/**/SKILL.md`;
   * `README.md`;
   * `.gitignore`;
   * relevant files under `docs/`;
   * current branch and worktree status.
3. Check whether any `AGENTS.md` files already exist.
4. Identify duplicated or conflicting instructions.
5. Preserve uncommitted user changes.
6. Do not modify runtime implementation files unless a broken documentation link requires a minimal correction.

Create a short internal implementation plan before editing.

---

# Instruction hierarchy

Establish and document this hierarchy:

```text
Root AGENTS.md
    ↓
Nearest scoped AGENTS.md
    ↓
Relevant skills/<skill-name>/SKILL.md
    ↓
Task-specific user instruction
```

Rules:

* `AGENTS.md` defines repository and directory-level constraints.
* `SKILL.md` defines reusable workflows for a specific class of work.
* A scoped `AGENTS.md` may add stricter requirements but must not weaken root safety rules.
* The user’s explicit task determines which Skill applies.
* Codex must not load or apply every Skill indiscriminately.
* When no Skill matches, Codex follows `AGENTS.md` and documents that no specialized Skill was used.
* Conflicts must be resolved in favor of the safer and more specific applicable instruction.
* Runtime code must never depend on `AGENTS.md` or `SKILL.md`.

---

# Required target structure

Create or update:

```text
AGENTS.md

skills/
  README.md
  drone-metashape-local-one-click/
    SKILL.md
  metashape-runtime-validation/
    SKILL.md
  metashape-diagnostic-analysis/
    SKILL.md

metashape_pipeline/
  AGENTS.md

web/
  AGENTS.md

tests/
  AGENTS.md

docs/
  codex-workflow.md
  repository-governance.md

.github/
  pull_request_template.md
  ISSUE_TEMPLATE/
    implementation.md
    bug-report.md
```

Adjust exact issue-template format only when justified.

Do not delete root `SKILLS.md`.

Mark it as legacy/reference documentation if appropriate and link readers to `AGENTS.md` and `skills/README.md`.

---

# Root `AGENTS.md`

Create a concise but complete root `AGENTS.md`.

It must cover the following.

## Repository purpose

Explain that this repository provides a local Windows one-click interface for running deterministic Agisoft Metashape Orthomosaic jobs.

Normal processing must run using scripts and the Metashape API, not Codex.

## Required reading

Before implementation, Codex must read:

1. root `AGENTS.md`;
2. the nearest scoped `AGENTS.md`;
3. the relevant `SKILL.md`;
4. files directly related to the task;
5. current tests and documentation.

Do not require Codex to read the entire repository for every small task.

## Skill selection table

Include a table similar to:

| Task                                                            | Required Skill                       |
| --------------------------------------------------------------- | ------------------------------------ |
| Application architecture, job profiles, local API, UI, launcher | `drone-metashape-local-one-click`    |
| Real Metashape version/API/CLI validation                       | `metashape-runtime-validation`       |
| Failed job logs and diagnostic packages                         | `metashape-diagnostic-analysis`      |
| Documentation-only or small maintenance task                    | No specialized Skill unless relevant |

## Repository workflow

Use:

```text
one issue = one branch = one pull request
```

Rules:

* inspect before modifying;
* keep the change scoped to the current task;
* do not mix unrelated refactors;
* run relevant tests;
* document untested behavior;
* human review and merge are mandatory;
* no automatic merge;
* no force push;
* no deployment unless explicitly requested;
* no branch deletion unless explicitly requested;
* no history rewriting;
* no changes to secrets or local configuration.

Do not require creation of an issue or PR when the user explicitly requests only local analysis or a prompt.

## Protected data and generated files

Codex must not commit:

* drone images;
* `.psx`;
* `.files/`;
* `.tif`;
* `.tiff`;
* reports generated from production data unless approved;
* job runtime directories;
* logs containing sensitive paths;
* diagnostics containing secrets;
* `config.local.json`;
* `.env`;
* Telegram tokens;
* license information;
* large generated outputs.

Respect `.gitignore`.

Do not delete user data or generated Metashape projects.

## Runtime constraints

* localhost only by default;
* no cloud upload of drone images;
* no arbitrary command execution;
* no `shell=True` with user-controlled input;
* no GUI click automation for Metashape;
* use the Metashape Python API;
* no silent overwrite;
* mock results must be visibly labeled;
* do not claim real Metashape validation without evidence.

## Legacy scripts

Files under `work/` are retained as migration references.

Do not delete or rewrite them unless a separate approved migration task explicitly requests it.

## Testing

Codex must:

* run targeted tests first;
* run the complete non-Metashape test suite when changing shared behavior;
* distinguish mock validation from real Metashape validation;
* report skipped or unavailable tests;
* never weaken a test only to obtain a passing result.

## Final report

Every implementation response should state:

* files changed;
* tests run;
* test results;
* mock-validated behavior;
* real-Metashape-validated behavior;
* unverified behavior;
* known risks;
* whether a PR, push, merge, deployment, or branch deletion occurred.

---

# Main application Skill

Review and improve:

```text
skills/drone-metashape-local-one-click/SKILL.md
```

Preserve useful existing content.

This Skill should apply to:

* application architecture;
* local API;
* `index.html`;
* launcher;
* job/profile/state schemas;
* mock adapter;
* deterministic pipeline;
* output safety;
* tests;
* documentation;
* non-version-specific Metashape integration.

It must explicitly exclude:

* real-version compatibility claims;
* direct diagnostic-only analysis;
* production data processing;
* automatic execution of AI-generated fixes.

Keep this Skill implementation-oriented and reusable.

Do not duplicate every root `AGENTS.md` rule. Reference root rules and add only task-specific workflow.

---

# Runtime validation Skill

Create:

```text
skills/metashape-runtime-validation/SKILL.md
```

Use valid YAML frontmatter:

```yaml
---
name: metashape-runtime-validation
description: Validate the drone-metashape application against an installed Agisoft Metashape version, including CLI invocation, Python runtime compatibility, API calls, hardware configuration, project creation, Orthomosaic export, and controlled failure behavior.
---
```

The Skill must require:

1. An approved Windows machine.
2. An installed licensed Metashape.
3. A copied or disposable test dataset.
4. Recording:

   * Metashape version/build;
   * Metashape embedded Python version;
   * Windows version;
   * CPU/GPU/RAM;
   * dataset size;
   * profile used.
5. Testing actual:

   * `metashape.exe -r` behavior;
   * argument passing;
   * import compatibility;
   * project creation;
   * photo loading;
   * alignment;
   * depth maps;
   * DEM;
   * Orthomosaic;
   * GeoTIFF export;
   * project save;
   * process close behavior.
6. Validation of CPU/GPU configuration.
7. Controlled failure testing.
8. Clear separation between:

   * passed;
   * warning;
   * failed;
   * not tested.
9. No use of production originals for the first validation.
10. No claim of production readiness based only on mock tests.

Include requirements for a report at:

```text
docs/real-metashape-validation.md
```

---

# Diagnostic analysis Skill

Create:

```text
skills/metashape-diagnostic-analysis/SKILL.md
```

Use valid YAML frontmatter:

```yaml
---
name: metashape-diagnostic-analysis
description: Analyze a failed drone Metashape job from its diagnostic package, identify the most likely failure stage and cause, distinguish configuration, data, environment, and code failures, and propose safe next actions without automatically executing changes.
---
```

The Skill must instruct Codex to inspect only the minimum necessary files:

```text
job.json
state.json
profile.json
error.txt
processing.log
environment.json
summary.md
```

Analysis workflow:

1. Verify the package belongs to one job.
2. Identify the failed stage.
3. Identify the last successful stage.
4. Check retry count.
5. Classify the likely cause:

   * source data;
   * path/permission;
   * disk/memory;
   * license;
   * Metashape version/API;
   * processing profile;
   * output conflict;
   * application bug;
   * unknown.
6. Separate direct evidence from inference.
7. Recommend the safest next action.
8. Do not automatically:

   * modify profiles;
   * restart a job;
   * overwrite output;
   * execute generated code;
   * delete projects.
9. When a source-code change is required, recommend a separate issue/branch/PR.
10. Produce a concise diagnostic report suitable for a non-technical operator.

---

# `skills/README.md`

Create a short Skill registry.

It should explain:

* what a Skill is;
* how Codex selects one;
* that Skills are development instructions, not runtime dependencies;
* available Skills;
* example task phrases that trigger each Skill;
* how to add a future Skill;
* naming convention;
* required YAML frontmatter;
* requirement to keep Skills focused and non-overlapping.

Include a registry table.

---

# Scoped pipeline `AGENTS.md`

Create:

```text
metashape_pipeline/AGENTS.md
```

It must apply to files under `metashape_pipeline/`.

Rules should include:

* normal Python and Metashape embedded Python compatibility must be treated separately;
* do not assume the same Python version;
* `Metashape` imports must remain isolated from normal test collection;
* no hard-coded plot paths;
* no arbitrary `eval`;
* map profile values through explicit allowlists;
* use argument arrays and `shell=False`;
* state writes must remain atomic;
* errors must persist stage evidence;
* fatal stages must stop later stages;
* no silent fallback to a lower quality profile;
* output overwrite requires an explicit policy;
* real adapter changes require mock regression tests plus real validation notes;
* keep mock adapter clearly distinguishable from production output;
* legacy scripts remain untouched unless specifically requested.

Reference the appropriate Skills rather than copying them in full.

---

# Scoped web `AGENTS.md`

Create:

```text
web/AGENTS.md
```

Rules:

* plain HTML/CSS/JavaScript unless an approved task changes this;
* no Node.js runtime dependency for normal use;
* Thai-first labels;
* desktop usability;
* localhost API only;
* no direct filesystem assumptions from browser APIs;
* do not expose secrets;
* do not fabricate progress percentages;
* show mock mode clearly;
* destructive actions require confirmation;
* unsupported features must be disabled or labeled, not presented as working;
* UI must use persisted backend state as the source of truth;
* maintain accessibility basics:

  * labels;
  * keyboard usability;
  * readable status;
  * clear error text.

---

# Scoped tests `AGENTS.md`

Create:

```text
tests/AGENTS.md
```

Rules:

* tests must not require a Metashape license unless explicitly marked as real integration tests;
* use temporary directories;
* mock outputs must be visibly fake;
* preserve Thai path tests;
* test security boundaries;
* test output conflict behavior;
* test terminal state handling;
* do not make tests depend on execution order;
* do not reduce assertions solely to pass;
* separate:

  * unit tests;
  * API tests;
  * mock end-to-end tests;
  * real Metashape integration tests.

Real integration tests should be excluded from the default test command unless explicitly enabled.

---

# Workflow documentation

Create:

```text
docs/codex-workflow.md
```

Document this workflow:

```text
Discuss requirement
    ↓
Create or select issue
    ↓
Select applicable Skill
    ↓
Create one task branch
    ↓
Codex inspects scoped files
    ↓
Codex implements only the issue
    ↓
Run tests
    ↓
Review diff
    ↓
Open PR
    ↓
Human review
    ↓
Human merge
```

Include example task categories:

* UI improvement;
* pipeline bug;
* diagnostic analysis;
* real Metashape compatibility;
* profile addition;
* documentation update.

Explain when a PR is not needed, such as read-only analysis.

Create:

```text
docs/repository-governance.md
```

Explain:

* instruction hierarchy;
* protected files;
* generated data policy;
* mock versus real validation;
* release-readiness rule;
* human approval points.

---

# GitHub templates

Create a concise pull request template requiring:

* task/issue;
* selected Skill;
* scope;
* files changed;
* tests;
* mock validation;
* real Metashape validation;
* risk;
* screenshots for UI changes;
* confirmation that no production data or secrets were committed.

Create issue templates for:

## Implementation

Fields:

* objective;
* user workflow;
* applicable Skill;
* acceptance criteria;
* excluded scope;
* test requirements;
* real Metashape required or not.

## Bug report

Fields:

* observed behavior;
* expected behavior;
* failed stage;
* application mode;
* Metashape version if relevant;
* diagnostic package available;
* reproduction steps;
* whether production data is involved.

Do not require users to paste tokens, full drone images, or sensitive logs into an issue.

---

# Root `SKILLS.md`

Do not delete it.

Review whether it currently mixes:

* runtime workflow;
* Codex behavior;
* automation behavior;
* historical implementation notes.

Add a short notice near the top, when appropriate:

```text
Repository agent instructions now live in AGENTS.md.
Reusable Codex workflows live under skills/.
This file is retained as legacy workflow reference.
```

Do not rewrite the entire legacy file during this task.

---

# Validation

Validate:

1. Every new `SKILL.md` has valid YAML frontmatter.
2. Root and scoped `AGENTS.md` links resolve.
3. No circular instructions exist.
4. Skill responsibilities do not substantially overlap.
5. `SKILLS.md` remains present.
6. No runtime source behavior changed.
7. No secrets or generated outputs were added.
8. Markdown links work.
9. Existing tests still pass.
10. The default application behavior is unchanged.

Run the existing non-Metashape test suite.

If tests cannot run, report the exact blocker.

---

# Safety

Do not:

* modify Metashape API calls;
* modify profiles;
* implement Phase 4.5;
* implement Phase 5;
* process a real drone dataset;
* run production Metashape jobs;
* delete legacy scripts;
* push;
* merge;
* deploy;
* force-push;
* delete branches;
* rewrite history;
* add secrets;
* commit generated job/output files.

This task should primarily change Markdown and GitHub template files.

---

# Acceptance criteria

This task is complete when:

1. Root `AGENTS.md` exists.
2. Root `AGENTS.md` clearly defines repository safety and workflow.
3. Existing main Skill is reviewed and remains available.
4. Runtime-validation Skill exists.
5. Diagnostic-analysis Skill exists.
6. `skills/README.md` explains Skill selection.
7. Pipeline, web, and tests have scoped `AGENTS.md`.
8. Codex workflow documentation exists.
9. Repository governance documentation exists.
10. PR and issue templates exist.
11. Root `SKILLS.md` is preserved.
12. Existing tests still pass.
13. Runtime code behavior was not changed.
14. No push, merge, deployment, or branch deletion occurred.

---

# Final response

Report:

1. Files created.
2. Files modified.
3. Instruction hierarchy.
4. Skills registered.
5. Scoped `AGENTS.md` behavior.
6. Tests run.
7. Test results.
8. Conflicts or duplicated instructions found.
9. Any decision that still requires human review.
10. Confirmation that runtime implementation was not modified.
11. Confirmation that Phase 4.5 and Phase 5 were not started.
12. Confirmation that no push, merge, deployment, force-push, or branch deletion occurred.

Do not include raw tool traces.
