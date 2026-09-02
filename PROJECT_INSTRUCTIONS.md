# FYP PROJECT — FULL UNDERSTANDING, IMPROVEMENT, MODERNISATION & GITHUB HANDOFF

## ROLE

Act as a combination of:

* Senior Software Engineer
* Senior Applied AI / ML Engineer
* Data Scientist
* ML Research Engineer
* Solution Architect
* Product Engineer
* Technical Reviewer
* Git/GitHub Maintainer
* Technical Writer

You are taking ownership of my old Final Year Project (FYP).

The project currently exists inside this Google Drive folder:

**GOOGLE DRIVE FOLDER:**
ONEDRIVE UKM/FYP

Your job is NOT merely to review the project.

Your job is to:

**UNDERSTAND → RECONSTRUCT → AUDIT → IMPROVE → IMPLEMENT → TEST → DOCUMENT → PACKAGE → PUBLISH**

the project end-to-end.

The final outcome should feel like a serious, modern engineering / AI project rather than an abandoned university assignment.

---

# 0. CORE OPERATING PRINCIPLE

Take ownership of the project.

Do not wait for me to tell you exactly what files to inspect or what improvements to make.

Explore the available material yourself.

Make reasonable engineering decisions autonomously.

Only stop and ask me a question when there is a **true blocker** where proceeding would risk:

* destroying important work,
* exposing confidential information,
* creating meaningful financial cost,
* choosing between fundamentally different project objectives,
* or performing an irreversible action without sufficient information.

For everything else:

**investigate → reason → decide → implement → validate → continue.**

Do not repeatedly come back to me with summaries asking whether you should proceed.

---

# 1. FIRST — INGEST EVERYTHING

Before modifying anything, thoroughly inspect the Google Drive folder.

Do not assume that the code alone represents the project.

Look for EVERYTHING that may contain useful context, including:

* source code
* notebooks
* datasets
* CSV / Excel files
* reports
* FYP thesis
* proposal
* literature review
* methodology
* slides
* diagrams
* architecture diagrams
* screenshots
* experiment results
* model outputs
* references
* research papers
* meeting notes
* supervisor comments
* README files
* requirement documents
* demo material
* videos
* UI mockups
* evaluation results
* miscellaneous files

Build an internal inventory.

For each important artifact determine:

1. What is it?
2. What role did it play?
3. Is it still relevant?
4. Does it contradict another artifact?
5. Does it contain requirements not reflected in the implementation?
6. Does it reveal unfinished work or intended functionality?

Do not start rewriting the project after inspecting only a few files.

Understand the project first.

---

# 2. RECONSTRUCT THE ORIGINAL FYP

Reverse-engineer what I originally attempted to build.

Produce a concise but complete mental model covering:

## Problem

* What problem was the FYP solving?
* Who was the intended user?
* Why did the problem matter?
* What research question / objective existed?

## Inputs

* What data was used?
* Where did the data come from?
* What features / signals were used?
* How was data cleaned and transformed?

## System

Identify:

* architecture
* components
* workflow
* models
* algorithms
* APIs
* frontend
* backend
* storage
* external dependencies
* training pipeline
* inference pipeline

## Output

Determine:

* what the system produces,
* what the user sees,
* how success was measured,
* and how the original demo likely worked.

## Research methodology

Understand:

* baselines
* experiments
* evaluation metrics
* train/test methodology
* assumptions
* limitations
* conclusions

If implementation and thesis disagree, investigate why rather than blindly trusting either one.

---

# 3. TRY TO RUN THE ORIGINAL PROJECT

Before redesigning it, attempt to reconstruct and run the existing implementation.

Determine:

* expected runtime
* programming language versions
* dependency versions
* required datasets
* configuration files
* environment variables
* external services
* hardware assumptions
* model files

Create the minimum environment necessary to reproduce the project.

Document failures.

Categorise each failure as:

* missing dependency
* obsolete dependency
* broken path
* missing dataset
* incompatible API
* outdated framework
* code defect
* environment issue
* missing secret
* undocumented assumption

Do not silently replace the old system before understanding why it stopped working.

---

# 4. CREATE A PROJECT BASELINE

Before improvements, establish the original baseline whenever possible.

Capture relevant measurements such as:

* accuracy
* precision
* recall
* F1
* ROC-AUC
* MAE
* RMSE
* inference latency
* training time
* memory usage
* model size
* throughput
* response quality
* task completion
* usability

Use metrics appropriate to the project.

This baseline becomes the comparison point for improvements.

If original results cannot be reproduced, explain precisely why.

---

# 5. PERFORM A DEEP AUDIT

Audit the project across multiple dimensions.

## A. Problem Definition

Ask:

* Is the original problem still meaningful?
* Is the scope clear?
* Is the proposed solution appropriate?
* Are there better ways to solve the same problem today?

---

## B. Data

Inspect:

* data quality
* missing values
* leakage
* imbalance
* duplicates
* outliers
* incorrect labels
* feature usefulness
* train/test contamination
* reproducibility
* sampling methodology
* preprocessing correctness

---

## C. Machine Learning / AI

If applicable, inspect:

* model choice
* baselines
* feature engineering
* hyperparameters
* loss functions
* evaluation methodology
* overfitting
* underfitting
* cross-validation
* inference pipeline
* model persistence
* explainability
* reproducibility

Question whether the original model is still the best choice.

Compare it conceptually against modern alternatives.

---

## D. Software Engineering

Review:

* project structure
* modularity
* code quality
* naming
* coupling
* duplication
* error handling
* configuration management
* dependency management
* logging
* testing
* security
* secrets
* type safety
* documentation

---

## E. Architecture

Determine whether the architecture is:

* unnecessarily complicated,
* overly coupled,
* difficult to reproduce,
* difficult to deploy,
* or poorly separated.

Propose a cleaner architecture where necessary.

---

## F. Product / UX

If the project contains an interface, evaluate:

* usability
* information hierarchy
* interaction flow
* accessibility
* clarity
* responsive behaviour
* loading states
* errors
* visual consistency

Do not make the UI look like generic AI-generated SaaS.

Prefer a restrained, professional, polished design.

---

## G. Research Quality

Evaluate whether the project would withstand stronger academic scrutiny.

Look for:

* unsupported claims
* weak comparisons
* missing baselines
* insufficient experiments
* improper metrics
* lack of ablations
* data leakage
* poor sample size
* conclusions not supported by evidence

---

# 6. IDENTIFY IMPROVEMENT OPPORTUNITIES

Do not immediately implement every idea.

First generate a comprehensive improvement backlog.

Classify improvements into:

### P0 — Critical

Things preventing the project from working correctly.

### P1 — High Impact

Major improvements to performance, architecture, reliability, research validity or usability.

### P2 — Strong Portfolio Improvements

Things that would significantly improve how impressive the project is to employers.

### P3 — Nice to Have

Useful but lower-value enhancements.

For every candidate improvement estimate:

* expected impact
* difficulty
* implementation risk
* dependencies
* whether measurable
* whether necessary for portfolio quality

---

# 7. EXPLORE MULTIPLE POSSIBLE DIRECTIONS

Do not lock onto the first solution.

Explore several possible modernisation paths.

For example:

### Option A

Minimal restoration and cleanup.

### Option B

Modernise the original architecture while preserving the FYP concept.

### Option C

Substantially improve the AI / ML methodology.

### Option D

Turn the FYP into a polished production-style application.

### Option E

Re-imagine part of the project using modern technologies while preserving the original research objective.

You may create additional options where relevant.

Compare them by:

* technical quality
* portfolio value
* implementation cost
* research integrity
* maintainability
* performance
* complexity
* novelty

Select the strongest direction.

Explain why internally and proceed.

---

# 8. PRESERVE THE ORIGINAL RESEARCH INTENT

This is important.

Do not modernise the project so aggressively that it becomes unrelated to my FYP.

Maintain traceability between:

**Original FYP → Identified limitation → Improvement → New implementation**

The final project should still clearly represent an evolved version of my original work.

---

# 9. IMPLEMENT THE IMPROVEMENTS

Now execute the selected plan.

You are authorised to:

* refactor
* reorganise directories
* rewrite weak modules
* replace obsolete dependencies
* fix bugs
* optimise pipelines
* improve preprocessing
* improve models
* improve APIs
* improve architecture
* improve UI
* add tests
* add validation
* add logging
* add configuration
* add error handling
* improve type safety
* add automation
* improve reproducibility
* remove dead code

However:

Do not remove valuable original work without first understanding why it exists.

---

# 10. AI / ML IMPROVEMENT LOOP

If this is an AI/ML project, use an empirical optimisation loop.

For each meaningful experiment:

1. Define hypothesis.
2. Implement experiment.
3. Run evaluation.
4. Compare against baseline.
5. Record result.
6. Keep improvements that are justified.
7. Reject changes that do not help.

Explore appropriate alternatives including where relevant:

* classical ML
* ensembles
* gradient boosting
* deep learning
* transformers
* pretrained models
* transfer learning
* modern embeddings
* multimodal models
* retrieval
* LLMs
* computer vision models
* improved feature engineering

But do NOT replace the solution with an LLM just because LLMs are modern.

Choose technology based on the problem.

---

# 11. PREVENT DATA LEAKAGE

Be extremely careful about:

* preprocessing before splitting
* duplicates between train/test
* target leakage
* temporal leakage
* patient/user/entity leakage
* image near-duplicates
* augmentation contamination
* test-set tuning

If you find leakage in the original FYP, correct it and document its effect.

---

# 12. REPRODUCIBILITY

The project should be reproducible by another engineer.

Aim for a workflow such as:

```bash
git clone ...
cd project
<install command>
<setup command>
<run command>
```

Where appropriate add:

* requirements.txt
* pyproject.toml
* package.json
* environment.yml
* Dockerfile
* .env.example
* Makefile
* scripts/
* config/
* tests/

Choose only what genuinely helps.

Do not overengineer.

---

# 13. TESTING

Add appropriate tests.

Potentially include:

* unit tests
* integration tests
* pipeline tests
* preprocessing tests
* schema validation
* API tests
* model smoke tests
* regression tests
* end-to-end tests

Test critical edge cases.

Do not claim the project works simply because the code compiles.

---

# 14. VERIFY END-TO-END

Before considering implementation complete:

Run the system from the cleanest environment practical.

Verify:

INPUT
↓
PROCESSING
↓
MODEL / LOGIC
↓
BACKEND
↓
OUTPUT
↓
USER EXPERIENCE

Ensure the main use case actually works.

---

# 15. GITHUB REPOSITORY DESIGN

Create or prepare a professional repository.

Use a clean structure appropriate for the technology.

Example only:

```text
project/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── docs/
├── src/
├── tests/
├── scripts/
├── configs/
├── data/
│   └── README.md
├── notebooks/
├── models/
├── assets/
└── results/
```

Adapt this to the project rather than blindly copying it.

---

# 16. DO NOT UPLOAD SENSITIVE OR UNNECESSARY FILES

Before pushing anything to GitHub, scan for:

* API keys
* credentials
* passwords
* tokens
* private URLs
* personal data
* confidential data
* private datasets
* huge binaries
* system-generated files
* cached files
* unnecessary checkpoints

Create an appropriate `.gitignore`.

If the dataset cannot legally/practically be uploaded, provide:

* instructions for obtaining it,
* expected directory structure,
* preprocessing instructions,
* and optionally a small safe sample.

Never expose secrets.

---

# 17. CREATE AN EXCELLENT README

The README should be portfolio-quality.

It should quickly answer:

### What is this?

One strong paragraph.

### Why does it exist?

Explain the problem.

### What does it do?

Explain the system.

### Architecture

Include an architecture diagram if appropriate.

### How it works

Describe the workflow.

### Results

Show measurable outcomes.

Prefer comparison:

| Approach         | Metric |
| ---------------- | -----: |
| Original FYP     |      X |
| Improved version |      Y |

### Demo

Include screenshots / GIF / video instructions where appropriate.

### Installation

Provide exact commands.

### Usage

Provide examples.

### Project structure

Explain important folders.

### Technical decisions

Explain major architectural choices.

### Original FYP vs Modernised Version

Clearly show what changed.

### Limitations

Be transparent.

### Future work

Only meaningful improvements.

### Author

Include my relevant information from available material.

The README should be understandable to:

* recruiters
* AI engineers
* software engineers
* researchers
* hiring managers

within a few minutes.

---

# 18. CREATE ARCHITECTURE DOCUMENTATION

Where appropriate create:

`docs/architecture.md`

Include:

* system architecture
* data flow
* component responsibilities
* model flow
* important design decisions
* deployment flow
* external dependencies

Use Mermaid diagrams where useful.

---

# 19. CREATE AN IMPROVEMENT / EVOLUTION DOCUMENT

Create something similar to:

`docs/fyp-evolution.md`

Document:

## Original system

What the FYP originally contained.

## Problems discovered

What was weak / outdated / broken.

## Improvements

What was changed.

## Evidence

What improved measurably.

## Modern architecture

What the project looks like now.

This document is important because I want to be able to explain this project during interviews.

---

# 20. CREATE AN INTERVIEW BRIEF FOR ME

Create:

`docs/interview-brief.md`

Teach me how to explain the project.

Include:

### 30-second explanation

### 2-minute explanation

### 5-minute technical explanation

### Problem

### Architecture

### Why these technologies?

### Hardest engineering problem

### Hardest AI / data problem

### Major trade-offs

### What went wrong originally?

### What did I improve?

### Results

### What would I do next?

### Likely interview questions

And strong factual answers grounded in the actual implementation.

Do not fabricate accomplishments.

---

# 21. MAKE THE PROJECT PORTFOLIO-WORTHY

Evaluate the final project as if I were applying for roles such as:

* Applied AI Engineer
* AI Engineer
* Machine Learning Engineer
* Data Scientist
* Software Engineer
* Data Engineer

Ask:

> If a strong engineer opened this GitHub repository for five minutes, would they be impressed?

Improve the repository until the answer is reasonably yes.

Focus particularly on signals employers care about:

* good problem formulation
* engineering judgment
* empirical evaluation
* clean architecture
* reproducibility
* thoughtful trade-offs
* tests
* documentation
* actual working software

Avoid adding complexity simply to make the repository look sophisticated.

---

# 22. GIT WORKFLOW

Preserve traceability.

Use meaningful commits rather than one enormous commit.

Example categories:

```text
chore: reconstruct original FYP environment

fix: repair data preprocessing pipeline

refactor: modularize model inference

feat: add improved evaluation pipeline

feat: implement improved model

test: add preprocessing and inference tests

docs: document architecture and FYP evolution
```

Do not fabricate commit history pretending modern work existed during the original FYP.

---

# 23. GITHUB PUBLISHING

Once the project is ready:

1. Determine whether an appropriate repository already exists.
2. If it exists, inspect it before modifying.
3. Preserve valuable existing history.
4. Prefer creating a working branch for major changes.
5. Commit the improvements.
6. Push to GitHub.
7. Verify the remote repository reflects the intended state.

Do NOT force-push or rewrite existing history unless absolutely necessary.

If creating a new repository is required, use a professional name based on the actual project.

---

# 24. VERIFY THE GITHUB REPOSITORY AFTER PUSHING

After publishing, inspect the repository as an external visitor would.

Check:

* README rendering
* broken links
* images
* Mermaid diagrams
* installation instructions
* directory structure
* accidental secrets
* unnecessary files
* large files
* missing documentation
* GitHub repository description
* topics/tags if available

Fix issues you discover.

---

# 25. QUALITY GATE

Do not call the work finished until these are addressed.

### Understanding

* [ ] Google Drive artefacts inspected
* [ ] Original FYP reconstructed
* [ ] Architecture understood
* [ ] Research methodology understood

### Baseline

* [ ] Original project execution attempted
* [ ] Baseline recorded where possible
* [ ] Failures documented

### Engineering

* [ ] Major defects fixed
* [ ] Architecture improved
* [ ] Dead code addressed
* [ ] Error handling reviewed
* [ ] Secrets removed
* [ ] Dependencies reproducible

### AI / Data

* [ ] Dataset methodology reviewed
* [ ] Leakage checked
* [ ] Model methodology reviewed
* [ ] Evaluation corrected where necessary
* [ ] Improvements benchmarked

### Validation

* [ ] Tests run
* [ ] Main workflow tested
* [ ] Regression risks reviewed

### Documentation

* [ ] README complete
* [ ] Architecture documented
* [ ] FYP evolution documented
* [ ] Interview brief created

### GitHub

* [ ] Repository structured professionally
* [ ] Git history meaningful
* [ ] No confidential files
* [ ] Changes pushed
* [ ] GitHub rendering verified

---

# 26. KEEP A WORKING PROJECT LOG

Maintain:

`docs/modernisation-log.md`

Update it during the work.

Use a structure similar to:

```markdown
# Modernisation Log

## Discovery

### Finding
...

### Evidence
...

### Decision
...

---

## Experiment 001

Hypothesis:
...

Change:
...

Baseline:
...

Result:
...

Decision:
KEEP / REJECT

---

## Engineering Decision

Problem:
...

Options considered:
...

Chosen approach:
...

Reason:
...
```

This prevents reasoning and discoveries from disappearing during a long task.

---

# 27. DECISION PHILOSOPHY

When choosing between solutions, optimise in approximately this order:

1. correctness
2. reproducibility
3. measurable performance
4. maintainability
5. simplicity
6. portfolio value
7. novelty

Novelty alone is not enough.

A boring solution that works extremely well is better than an unnecessarily exotic architecture.

---

# 28. DO NOT FAKE RESULTS

This is critical.

Never invent:

* experiments
* accuracy
* performance improvements
* test results
* datasets
* metrics
* research findings
* benchmarks

Clearly separate:

**Measured**

from

**Estimated**

from

**Suggested future work.**

---

# 29. WORK AUTONOMOUSLY

Once enough context has been gathered, continue through the project without repeatedly asking:

* "Would you like me to proceed?"
* "Should I implement this?"
* "Do you want me to continue?"
* "Would you like me to push it?"

The objective already authorises the complete workflow.

Only interrupt me for a genuine blocker.

---

# 30. FINAL DELIVERABLE

When everything is complete, give me one concise executive handoff containing:

## 1. What my original FYP was

Explain it in plain English.

## 2. Original architecture

Summarise how it worked.

## 3. Problems discovered

Highlight the most important findings.

## 4. Improvements implemented

List meaningful changes.

## 5. Performance comparison

Show before vs after wherever measurements exist.

## 6. Final architecture

Explain the modernised system.

## 7. Validation

State exactly what was tested and passed.

## 8. GitHub

Provide:

* repository
* branch
* meaningful commits
* final status

## 9. Remaining limitations

Be transparent.

## 10. Portfolio assessment

Rate the final project from:

**1–10 for portfolio readiness**

and explain what prevents it from being a 10/10, if anything.

## 11. How I should explain it in interviews

Give me the strongest concise narrative based on what was actually built.

---

# ULTIMATE OBJECTIVE

I do not want a superficial cleanup of an old university project.

I want you to take my FYP, deeply understand what I originally tried to accomplish, determine what was good and bad about it, reconstruct it, improve it using today's engineering and AI practices where justified, validate those improvements empirically, turn it into a polished and reproducible project, document the evolution from university FYP to modern implementation, and publish the finished project to my GitHub.

Treat this like you inherited the project as its new senior engineer.

Do the work end-to-end.

---

# 0.1 — CREATE A PERSISTENT LOCAL WORKSPACE & SAVE THESE INSTRUCTIONS

Before doing any substantial analysis or implementation, create a dedicated **local working folder** for this project.

The original FYP material is currently located at:

`ONEDRIVE UKM/FYP`

Treat that location primarily as the **source / historical archive**.

Do not perform large-scale destructive edits directly against the original FYP files.

Instead:

1. Inspect the original files.
2. Determine the appropriate project structure.
3. Create a dedicated local working directory.
4. Copy or reconstruct the files required for the modernised project into that workspace.
5. Perform development, refactoring, experimentation, testing, documentation and Git operations from the local workspace.

Choose a sensible professional folder name based on the actual FYP once you understand what the project is.

For example:

```text
~/Projects/<fyp-project-name>/
```

or an equivalent appropriate local development directory for the machine.

Do not blindly use this exact path if the environment has an established projects/workspace directory. Inspect the environment first and choose the most appropriate location.

---

## PRESERVE THE ORIGINAL FYP

The original FYP folder should act as historical source material.

Unless absolutely necessary:

**DO NOT overwrite, delete, rename or reorganise the original FYP source material.**

The modernised implementation should live separately.

Maintain traceability between:

```text
Original FYP
    ↓
Local reconstructed baseline
    ↓
Modernisation work
    ↓
Final GitHub repository
```

If something from the original FYP is modified, migrated, rewritten or discarded, record why.

---

## SAVE THIS MASTER INSTRUCTION LOCALLY

One of your FIRST actions after creating the local workspace must be to save the complete instruction I have given you into the project itself.

Create:

```text
PROJECT_INSTRUCTIONS.md
```

at the root of the local project.

This file must contain the **complete operating instruction for this FYP modernisation task**, including:

* project objective
* operating principles
* autonomy rules
* discovery requirements
* FYP reconstruction requirements
* baseline requirements
* audit requirements
* AI/ML experimentation rules
* implementation rules
* testing requirements
* documentation requirements
* Git/GitHub requirements
* portfolio objectives
* quality gates
* final deliverables

Do NOT reduce it to a tiny summary.

Preserve enough detail that another capable coding agent could open the project with zero previous conversation context, read `PROJECT_INSTRUCTIONS.md`, and understand what it is expected to accomplish.

This file is the persistent **mission specification** for the entire project.

---

## READ THE INSTRUCTION BEFORE CONTINUING WORK

At the beginning of every new working session, resumed session, context reset, agent handoff, or substantial continuation of this project:

**FIRST READ:**

```text
PROJECT_INSTRUCTIONS.md
```

Then inspect the current project state before making changes.

Do not rely solely on conversational memory.

If your active context ever becomes uncertain about:

* what the objective is,
* what has already been completed,
* what constraints exist,
* what you were supposed to do next,
* or what quality standard is expected,

return to:

```text
PROJECT_INSTRUCTIONS.md
```

and the project tracking files before proceeding.

---

## CREATE PERSISTENT PROJECT MEMORY

In addition to the master instruction, maintain persistent state inside the repository so work can survive:

* long-running sessions
* context compaction
* agent handoffs
* model changes
* interrupted work
* machine restarts
* future continuation

Create and maintain:

```text
PROJECT_INSTRUCTIONS.md
TASKS.md
docs/modernisation-log.md
docs/project-state.md
```

Their responsibilities are:

### `PROJECT_INSTRUCTIONS.md`

**What are we supposed to accomplish?**

This is the stable master instruction.

Do not constantly rewrite it based on temporary discoveries.

---

### `TASKS.md`

**What needs to be done?**

Maintain an actionable checklist.

Example:

```markdown
# FYP Modernisation Tasks

## Discovery
- [x] Inventory original FYP files
- [x] Read thesis
- [x] Identify original codebase
- [ ] Reconstruct environment

## Baseline
- [ ] Run original model
- [ ] Reproduce reported metric
- [ ] Validate train/test methodology

## Improvements
- [ ] Evaluate architecture alternatives
- [ ] Implement selected model improvements
- [ ] Benchmark against baseline

## Engineering
- [ ] Refactor project structure
- [ ] Add tests
- [ ] Add configuration management

## Portfolio
- [ ] Complete README
- [ ] Add architecture diagram
- [ ] Add results comparison
- [ ] Prepare demo

## GitHub
- [ ] Security scan
- [ ] Final validation
- [ ] Push repository
```

Update it continuously.

Do not mark something complete unless it has actually been completed.

---

### `docs/modernisation-log.md`

**What did we discover, try and decide?**

Maintain the detailed working history already required elsewhere in this instruction.

Record:

* discoveries
* experiments
* failures
* measurements
* architectural decisions
* rejected alternatives
* implementation decisions
* important debugging findings

---

### `docs/project-state.md`

**Where are we right now?**

Keep this concise and current.

It should contain something similar to:

```markdown
# Current Project State

## Current Phase
Baseline reconstruction

## Last Completed
Original dataset pipeline reconstructed successfully.

## Currently Working On
Reproducing the original model evaluation.

## Important Findings
- Original project used ...
- Thesis reported ...
- Implementation differs because ...
- Potential leakage identified in ...

## Current Baseline
...

## Major Decisions
...

## Known Blockers
None.

## Next Actions
1. ...
2. ...
3. ...

## Last Verified
<date / commit>
```

Update this file whenever there is a meaningful change in project state.

---

# CONTEXT RECOVERY PROTOCOL

If work is resumed without reliable memory of previous activity, do NOT start rediscovering everything from scratch.

Use this recovery sequence:

```text
1. Read PROJECT_INSTRUCTIONS.md
        ↓
2. Read docs/project-state.md
        ↓
3. Read TASKS.md
        ↓
4. Read recent sections of docs/modernisation-log.md
        ↓
5. Inspect git status
        ↓
6. Inspect recent git history
        ↓
7. Continue from the next unfinished task
```

This is the canonical recovery procedure.

---

# GIT AS PROJECT MEMORY

Once Git has been initialised, also use Git history as part of the persistent project memory.

Before continuing unfamiliar work, inspect:

```bash
git status
git log --oneline --decorate -20
```

and relevant diffs where necessary.

Commits should make it possible to understand how the project evolved.

Do not use vague commit messages such as:

```text
update
changes
fix stuff
final
final2
new version
```

Use commits that explain meaningful changes.

---

# CHECKPOINT BEFORE LARGE CHANGES

Before performing a substantial architectural rewrite, model replacement or major refactor:

1. Ensure the current working state is understood.
2. Record the intended change in the modernisation log.
3. Ensure the previous reproducible state is preserved through Git whenever practical.
4. Then proceed.

This allows failed experiments to be safely reverted without losing the reconstructed FYP.

---

# DO NOT LOSE KNOWLEDGE

Important discoveries must not exist only inside your temporary reasoning context.

If you discover something that would matter to a future engineer working on this project, persist it in the appropriate project documentation.

Examples:

* why a model was selected
* why another approach failed
* unusual dataset behaviour
* hidden preprocessing assumptions
* environment quirks
* original FYP inconsistencies
* important metrics
* leakage discovered
* dependency compatibility issues
* design trade-offs
* deployment constraints
* unresolved limitations

Use this principle:

> **Conversation is temporary. The repository is the source of truth.**

By the end of the project, someone should be able to clone/open the repository, read the documentation and Git history, and reconstruct not only **what was built**, but also **why it was built that way**.

---

# INITIAL BOOTSTRAP SEQUENCE

Therefore, your initial workflow should approximately be:

```text
Locate ONEDRIVE UKM/FYP
        ↓
Inspect environment
        ↓
Inventory original FYP
        ↓
Determine project identity
        ↓
Create local project workspace
        ↓
Create PROJECT_INSTRUCTIONS.md
        ↓
Create TASKS.md
        ↓
Create docs/project-state.md
        ↓
Create docs/modernisation-log.md
        ↓
Record initial project state
        ↓
Begin deep FYP reconstruction
        ↓
Continue through the complete modernisation workflow
```

Do not treat creation of these files as the completion of the project.

They exist so you can reliably execute the much larger mission defined in this instruction without losing direction.

