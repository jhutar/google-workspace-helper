# Implementation Plan: Export Spreadsheets and Slides to Markdown

**Branch**: `002-support-sheets-slides-export` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-support-sheets-slides-export/spec.md`

## Summary
Add robust support for exporting Google Spreadsheets and Presentations (Slides) directly to Markdown format. Due to limitations in the Google Drive API, the system implements a custom fallback pipeline:
1. **Spreadsheets**: Fetched as standard CSV via `gws` and parsed into clean Markdown tables in the post-processing stage.surfaces a warning notice to `stderr`.
2. **Presentations**: Downloaded as PPTX and converted to Markdown slides using local `pandoc` invocation, failing fast with a descriptive help error if `pandoc` is not installed on the system.
3. **Logging**: Configured to write verbose `DEBUG` logs to `google-workspace-helper.log` while showing standard warning-level outputs to `stderr`.

---

## Technical Context

**Language/Version**: Python >=3.12

**Primary Dependencies**: Built-in standard libraries (`logging`, `csv`, `json`, `subprocess`, `argparse`, `shutil`), external subprocesses (`gws`, `pandoc`).

**Storage**: Local file storage for the generated Markdown outputs, log files, and transient temporary conversion directories.

**Testing**: `pytest` and `unittest.mock` for mocking subprocess actions.

**Target Platform**: Multi-platform (Linux, macOS, Windows) where `gws` and `pandoc` are installed.

**Project Type**: CLI utility tool.

**Performance Goals**: Converting a spreadsheet or slide deck to Markdown completes in under 5 seconds.

**Constraints**:
- Pandoc must not be packaged as a direct python dependency; executed as a shell subprocess.
- No third-party CSV styling libraries are added.
- All temporary raw PPTX and CSV conversion files must be cleaned up on success.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Python Best Practices & PEP 8 Standards** - `ruff check` and `ruff format` are integrated via pre-commit. Checked: ✅ Pass.
- **Principle II: Right Repository Layout** - Code follows the clean `src/` layout with isolated test structures in `tests/`. Checked: ✅ Pass.
- **Principle III: Testable and Maintainable Code** - Functions for CSV-to-Markdown, PPTX-to-Markdown, and logging configurations are decoupled and testable in isolation. Checked: ✅ Pass.
- **Principle IV: Fail Fast** - Pre-execution checks assert `pandoc` availability and correct MimeTypes immediately, failing fast if prerequisites are not met. Checked: ✅ Pass.
- **Principle V: No Assumptions** - File metadata and API contracts are queried and verified explicitly before execution. Checked: ✅ Pass.

---

## Project Structure

### Documentation (this feature)

```text
specs/002-support-sheets-slides-export/
├── plan.md              # This file
├── research.md          # Design decisions and technology evaluation
├── data-model.md        # Entities and state transitions
├── quickstart.md        # Run scenarios and expected outcomes
└── contracts/
    └── cli.md           # CLI interface contract
```

### Source Code (repository root)

```text
src/
└── google_workspace_helper/
    ├── __init__.py
    ├── cli.py           # Argument parsing and entrypoints
    ├── exporter.py      # Metadata querying, file downloads, and pandoc invocation
    ├── postprocessor.py # CSV parsing to Markdown tables and cleanup
    └── logging_config.py# Application logging setup (DEBUG to file, WARN to stderr)

tests/
├── test_cli.py
├── test_exporter.py
├── test_postprocessor.py
└── test_logging_config.py
```

**Structure Decision**: Code changes are added to the existing standard layout, with the logging module decoupled to `logging_config.py` to maintain modularity.
