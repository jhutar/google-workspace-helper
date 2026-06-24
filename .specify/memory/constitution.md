<!--
SYNC IMPACT REPORT
==================
Version Change: [none] -> 1.0.0
Bump Rationale: Initial ratification of the constitution defining Python project standards, repository layout, and testing/fail-fast governance.
Modified Principles:
  - I. Python Best Practices & PEP 8 Standards (Added)
  - II. Right Repository Layout (Added)
  - III. Testable and Maintainable Code (Added)
  - IV. Fail Fast (Added)
  - V. No Assumptions (Added)
Added Sections:
  - Coding Standards and Linting (Section 2)
  - Development Workflow and Quality Gates (Section 3)
Removed Sections:
  - None
Templates Checked/Updated:
  - .specify/templates/plan-template.md: ✅ updated (no placeholders needing manual update, aligns with principles)
  - .specify/templates/spec-template.md: ✅ updated (no placeholders needing manual update, aligns with principles)
  - .specify/templates/tasks-template.md: ✅ updated (no placeholders needing manual update, aligns with principles)
Follow-up TODOs:
  - None (All placeholders successfully filled with concrete text)
-->

# Google Cloud CLI (gcloud-cli) Constitution

## Core Principles

### I. Python Best Practices & PEP 8 Standards
The codebase MUST strictly adhere to PEP 8 standards, leverage robust static typing (via `mypy`), and utilize idiomatic Python patterns. All code formatting and linting rules MUST be enforced automatically (e.g., via Ruff or Black and isort).
**Rationale**: Adhering to unified styling and static analysis prevents common runtime bugs, reduces cognitive load, and ensures the codebase remains maintainable as complexity grows.

### II. Right Repository Layout
The repository MUST follow the standard Python `src/` layout (with source code in `src/` and tests in `tests/`). The structure must strictly separate core library business logic from CLI interface/presentation layers and API routers.
**Rationale**: Clean separation of directories avoids circular imports, prevents layout pollution, simplifies packaging, and makes testing components in isolation straightforward.

### III. Testable and Maintainable Code
Every new feature or bug fix MUST have corresponding tests (unit, contract, or integration tests). Code MUST be structured for testability—avoiding global state, utilizing dependency injection, and keeping functions/classes small with single responsibilities.
**Rationale**: High-quality automated test suites ensure long-term stability and confidence. Designing for testability naturally leads to decoupled, modular, and maintainable software architecture.

### IV. Fail Fast
The application MUST validate all input parameters, configuration variables, and environment dependencies immediately at startup or at the boundaries of public interfaces. Invalid states or invalid inputs MUST raise explicit, descriptive exceptions immediately rather than returning null or failing silently.
**Rationale**: Catching invalid data or unexpected environments early prevents corrupted states, reduces debugging effort, and ensures robust error containment.

### V. No Assumptions (Explicit over Implicit)
Developers MUST NOT assume that remote services, database schemas, or system configurations are always correct or available. All system schemas and API boundaries MUST be validated explicitly (e.g., using type-safe validation libraries like Pydantic).
**Rationale**: Explicit verification of configurations and system contracts prevents silent failures and ensures clear boundary enforcement across complex dependencies.

## Coding Standards and Linting
1. Static Type Checking: All Python files MUST have 100% type annotations and pass strict static type-checking gates (such as `mypy --strict`).
2. Code Formatter & Linter: Code formatting MUST be run automatically using standard ecosystem tools (e.g., `ruff check` and `ruff format`). No code containing linting errors or formatting violations can be merged.
3. Import Management: Imports MUST be grouped logically (standard library, third-party, local) and sorted.

## Development Workflow and Quality Gates
1. Testing Coverage: Minimum acceptable branch and statement test coverage is 90%. Any new pull request MUST NOT lower the existing overall code coverage.
2. Code Review Requirements: All pull requests require at least one approving review. Pull requests MUST pass all CI tests (formatting, linting, type-checking, and test suite execution) before merge.
3. Empirical Defect Verification: For any bug fix, the developer MUST first write a failing test that reproduces the defect, verify its failure, and then implement the fix to make the test pass.

## Governance
1. Primacy of Constitution: This Constitution supersedes all other documentation, practices, and informal conventions in the repository. All contributions MUST comply with its mandates.
2. Amendment Procedure: Amendments to this Constitution require a formal revision of `.specify/memory/constitution.md` via a pull request. The version MUST be bumped semantically: MAJOR for backward-incompatible rule changes, MINOR for new principles/sections, and PATCH for minor wording updates.
3. Compliance Verification: The implementation plan, specification documents, and checklists MUST verify compliance with all five Core Principles. Any deviation or exceptional case MUST be explicitly documented and justified under the 'Complexity Tracking' section of the implementation plan.

**Version**: 1.0.0 | **Ratified**: 2026-06-24 | **Last Amended**: 2026-06-24
