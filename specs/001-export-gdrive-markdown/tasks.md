# Tasks: Google Drive Markdown Exporter

**Input**: Design documents from `/specs/001-export-gdrive-markdown/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included as requested by implementation plan.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Story label mapping to spec (e.g. [US1], [US2], [US3])
- Exact file paths included in descriptions

---

## Phase 1: Setup

**Purpose**: Project initialization, directory structure, and linting toolchain setup.

- [x] T001 Create project directories `src/google_workspace_helper/` and `tests/`
- [x] T002 Initialize empty modules at `src/google_workspace_helper/__init__.py` and `tests/__init__.py`
- [x] T003 [P] Create pre-commit config at `.pre-commit-config.yaml` with Ruff, Bandit, and YAML linting
- [x] T004 [P] Create project execution entrypoint at `Makefile` to automate bootstrapping, testing, and checks

---

## Phase 2: Foundational

**Purpose**: Core dependency verification and basic CLI routing shell.

- [x] T005 Implement `gws` command presence verification on system PATH in `src/google_workspace_helper/exporter.py`
- [x] T006 [P] Create argparse routing shell framework in `src/google_workspace_helper/cli.py`

**Checkpoint**: Core setup complete. Code quality checks (`make check-all`) execute cleanly.

---

## Phase 3: User Story 1 - Export Google Doc (Priority: P1) 🎯 MVP

**Goal**: Export standard text Google Documents using file ID to clean markdown file via `gws`.

**Independent Test**: Running `google-workspace-helper export <id>` outputs correct markdown file without crashing.

### Tests for User Story 1

- [x] T007 [P] [US1] Create CLI argparse validation test cases in `tests/test_cli.py`
- [x] T008 [P] [US1] Create subprocess execution and mock `gws` test cases in `tests/test_exporter.py`

### Implementation for User Story 1

- [x] T009 [P] [US1] Implement argparse export subcommand with target options in `src/google_workspace_helper/cli.py`
- [x] T010 [US1] Implement `subprocess.run` wrapper to execute `gws drive files export` in `src/google_workspace_helper/exporter.py`
- [x] T011 [US1] Connect CLI commands to the exporter module and verify end-to-end text exports in `src/google_workspace_helper/cli.py`

**Checkpoint**: Standard document export is functional and completely covered by unit tests.

---

## Phase 4: User Story 2 - Post-process Images (Priority: P1) 🎯 MVP

**Goal**: Extract inline base64 images from markdown, write to `/tmp/<doc_id>/`, and rewrite links.

**Independent Test**: Running export on document with images yields no base64 in output and creates folder in `/tmp/`.

### Tests for User Story 2

- [x] T012 [P] [US2] Create base64 extraction and pattern replacement test cases in `tests/test_postprocessor.py`

### Implementation for User Story 2

- [x] T013 [P] [US2] Implement regex base64 URI matching and image decoding in `src/google_workspace_helper/postprocessor.py`
- [x] T014 [US2] Implement secure directory `/tmp/<doc_id>/` creation and binary write logic in `src/google_workspace_helper/postprocessor.py`
- [x] T015 [US2] Integrate the image extraction post-processing step into the main CLI export pipeline in `src/google_workspace_helper/cli.py`

**Checkpoint**: Base64 images are cleanly parsed, extracted locally, and properly cross-referenced.

---

## Phase 5: User Story 3 - Spreadsheets and Slides (Priority: P2)

**Goal**: Support Google Spreadsheets and Google Slides exports with table formats and image extraction.

**Independent Test**: Exporting Spreadsheet ID yields GFM tables and Slides ID yields slide page headers.

### Tests for User Story 3

- [x] T016 [P] [US3] Create specific Sheet and Slides test assertions inside `tests/test_exporter.py`

### Implementation for User Story 3

- [x] T017 [US3] Add mime-type detection and spreadsheet/slides formatting options to the subprocess call in `src/google_workspace_helper/exporter.py`
- [x] T018 [US3] Verify correct GFM table layout outputs for spreadsheets and slide sections for presentations

**Checkpoint**: Spreadsheets and Slides export capabilities fully validated.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Error containment, user experience refinements, and quality gates enforcement.

- [x] T019 Implement fail-fast exception wrapper to suppress complex Python stacktraces for command-line users
- [x] T020 Run entire quality suite (`make check-all` and `make test`) ensuring 100% linter passes and coverage >= 90%

---

## Dependencies

```text
Phase 1 (Setup)
      │
      ▼
Phase 2 (Foundational)
      │
      ▼
Phase 3 (User Story 1 - Export)
      │
      ▼
Phase 4 (User Story 2 - Image Post-processing)
      │
      ▼
Phase 5 (User Story 3 - Sheets & Slides)
      │
      ▼
Phase 6 (Polish)
```

---

## Parallel Execution

Multiple independent tasks can be executed concurrently to accelerate delivery:
- **Phase 1**: `T003` (Pre-commit setup) and `T004` (Makefile setup)
- **Phase 3**: `T007` (CLI tests) and `T008` (Exporter tests)
- **Phase 4**: `T012` (Postprocessor tests) and `T013` (MIME/base64 decoding helper)

---

## Implementation Strategy

1. **MVP Focus**: Build User Story 1 and User Story 2 first. This establishes the critical path (text export + base64 cleanup) allowing immediate consumption by AI agents.
2. **Incremental Delivery**: Commit and verify each phase independently, running the automated test suite frequently.
