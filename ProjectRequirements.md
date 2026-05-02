## PythonProp — Project Engineering Requirements

**Purpose:** PythonProp is an open-source Python port of Brendan Epps and Richard Kimball’s OpenProp (MATLAB). The project will remain community-buildable, contributor-friendly, and scientifically defensible.

### Licensing & Freedom
- **(Free/Libre):** The project shall be free to use, modify, and distribute.
- **(License continuity):** PythonProp shall be licensed under **GNU GPL v3.0**, extending OpenProp’s original GPL-3.0 licensing.
- **(No paid toolchain dependency):** The core workflow shall not require paid software licenses (no required MATLAB license).
- **(Redistribution):** It shall be possible to redistribute source and built artifacts in a GPL-compliant way.

### Usability
- **(Easy install):** Users shall be able to install/run using a standard Python workflow (e.g., `python -m venv` + `pip install -r requirements.txt`).
- **(Quick start):** A new user shall be able to produce a first result by following a Quick Start in ≤ 10 minutes.
- **(Good errors):** Common failures (missing deps, bad inputs) shall produce actionable error messages.

### Expandability & Architecture
- **(Modular design):** Core computation, IO, plotting, and UI shall be separated into modules with clear interfaces.
- **(Extensible models):** It shall be straightforward to add new analysis methods, geometry definitions, or output formats without rewriting core code.
- **(Stable public API):** Provide a small, documented API surface for programmatic use, and document breaking changes.
- **(Configuration):** Runs should be configurable via files (JSON/YAML/TOML) or structured Python objects—not hard-coded constants.

### Verification, Validation, and Reproducibility
- **(Verifiable):** Python results shall be comparable to original OpenProp outputs for equivalent inputs.
- **(Test suite):** The project shall include automated tests (unit + regression tests).
- **(Golden cases):** Maintain benchmark inputs/outputs and tolerances for numeric comparisons.
- **(Deterministic runs):** Given the same inputs and version, the software should produce repeatable results within defined numerical tolerance.
- **(Traceability):** Each release shall document changes and any known differences vs OpenProp.

### Documentation
- **(User docs):** Document installation, GUI usage, scripted usage, and example workflows.
- **(Developer docs):** Document repo structure, coding standards, and how to add features/tests.
- **(Attribution):** Document OpenProp heritage and include proper attribution and license references.

### Performance & Portability
- **(Reasonable runtime):** Typical analyses should run in practical time on a consumer laptop.
- **(Cross-platform):** Support Windows, macOS, and Linux where feasible.
- **(Supported Python versions):** Define and publish the supported Python version range (e.g., 3.10+).

### Collaboration & Project Management
- **(Contributor-friendly):** Provide “good first issue” tasks and clear contribution guidance.
- **(Code review):** Changes should be made via PRs with review when possible.
- **(Style/lint):** Use formatting/linting tooling to keep contributions consistent.
- **(Changelog/releases):** Tag releases and maintain a changelog.
