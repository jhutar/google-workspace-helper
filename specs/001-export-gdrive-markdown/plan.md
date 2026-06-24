# Implementation Plan: Google Drive Markdown Exporter

**Branch**: `001-export-gdrive-markdown` | **Date**: 2026-06-24 | **Spec**: [specs/001-export-gdrive-markdown/spec.md](spec.md)

**Input**: Feature specification from `/specs/001-export-gdrive-markdown/spec.md`

## Summary
Build a Python 3.12 CLI wrapper script named `google-workspace-helper` around the `gws` CLI tool that exports Google Drive documents, spreadsheets, and slides to clean markdown, post-processes inline base64 images into a dedicated `/tmp/<doc_id>/` directory, and properly links them within the final document. Development will use uv, pre-commit, and Makefile.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Standard library only (argparse, subprocess, re, base64, urllib, os, sys, pathlib). Testing depends on `pytest`. Development depends on `pre-commit` (ruff, bandit, gitleaks, yamllint, shellcheck).

**Storage**: Local file system write at target output path and temporary image extraction folder `/tmp/<doc_id>/`.

**Testing**: `pytest` for unit and integration testing. Mocking subprocesses to intercept and stub `gws` CLI calls.

**Target Platform**: Linux, macOS

**Project Type**: CLI wrapper

**Performance Goals**: Fast startup, zero third-party module imports overhead, image extraction overhead proportional to image size only.

**Constraints**: Thin wrapper; must call local authenticated `gws` command; cleanly decode dynamic base64 images without corruptions; prevent arbitrary shell injections from input file IDs.

**Scale/Scope**: Focuses on standard Google Documents, Spreadsheets, and Slides. Handles document sizes with typical image workloads safely within standard process limits.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Python Best Practices & PEP 8 Standards**: Pass. Ruff format & linter, strict static type checking with mypy will be initialized.
- **Right Repository Layout**: Pass. Matches Python `src/` layout convention with distinct tests.
- **Testable and Maintainable Code**: Pass. Module dependencies decoupled, test suites verify CLI parsing, image parsing, and subprocess calling separately.
- **Fail Fast**: Pass. CLI argument parser and validators verify parameters immediately.
- **No Assumptions**: Pass. Verify `gws` presence in PATH at startup.

## Project Structure

### Documentation (this feature)

```text
specs/001-export-gdrive-markdown/
├── spec.md              # Feature specification
├── plan.md              # This implementation plan
├── research.md          # Technology decisions
├── data-model.md        # Process states & entity definitions
├── quickstart.md        # Verification runbook
├── contracts/
│   └── cli.md           # CLI interface contract
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
src/
└── google_workspace_helper/
    ├── __init__.py
    ├── cli.py           # argparse entry point & subcommand routing
    ├── exporter.py      # gws subprocess execution wrapper
    └── postprocessor.py # base64 image parsing, extraction, and rewrites

tests/
├── __init__.py
├── test_cli.py          # CLI parser unit tests
├── test_exporter.py     # Subprocess calling & mock tests
└── test_postprocessor.py# Base64 image decoding & replacement tests

.pre-commit-config.yaml  # Static analysis & PEP 8 automated linting
Makefile                 # Standard build and run goals
```

**Structure Decision**: Option 1 (Single Project) layout, fully isolating source files into a dedicated python package `google_workspace_helper` under `src/`, with matching testing module under `tests/`.

## Complexity Tracking

*No violations identified. No tracking entries required.*
