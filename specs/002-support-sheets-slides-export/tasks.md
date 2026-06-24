# Tasks: Export Spreadsheets and Slides to Markdown

**Input**: Design documents from `/specs/002-support-sheets-slides-export/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/cli.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and logging configuration setup.

- [X] T001 Configure application logging infrastructure (DEBUG level to log file, WARNING/WARN level to stderr) in `src/google_workspace_helper/logging_config.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Implement file MimeType detection and verification from metadata using `gws drive files get` in `src/google_workspace_helper/exporter.py`
- [X] T003 Update CLI router to dispatch spreadsheet/presentation types to their respective processors in `src/google_workspace_helper/cli.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Export Google Spreadsheet to Markdown Table (Priority: P1) 🎯 MVP

**Goal**: Detect spreadsheet file type, export to CSV via `gws`, convert CSV to a standard Markdown table, log multi-sheet warning to `stderr`, and clean up intermediate CSV files on success.

**Independent Test**: Run exporter on a valid Google Spreadsheet ID and verify generated markdown file has clean Markdown table.

### Tests for User Story 1

- [X] T004 [P] [US1] Create unit tests for CSV-to-Markdown table parsing and formatting in `tests/test_postprocessor.py`

### Implementation for User Story 1

- [X] T005 [US1] Implement custom CSV parsing and Markdown table generation in `src/google_workspace_helper/postprocessor.py`
- [X] T006 [US1] Implement Google Spreadsheet CSV download and warning dispatch logic in `src/google_workspace_helper/exporter.py`
- [X] T007 [US1] Add temporary CSV cleanup handler on success in `src/google_workspace_helper/postprocessor.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Export Google Presentation/Slides to Markdown via Pandoc (Priority: P1)

**Goal**: Detect presentation type, download as PPTX via `gws`, check for local `pandoc` availability, convert PPTX to Markdown slides via subprocess `pandoc`, and delete intermediate PPTX files on success.

**Independent Test**: Run exporter on a valid Slides ID with `pandoc` installed and verify slide sections are successfully generated.

### Tests for User Story 2

- [X] T008 [P] [US2] Create unit tests for Slide pptx-to-markdown Pandoc wrapper in `tests/test_exporter.py`

### Implementation for User Story 2

- [X] T009 [US2] Implement local Pandoc verification and subprocess execution logic in `src/google_workspace_helper/exporter.py`
- [X] T010 [US2] Implement temporary PPTX download and warning handling for missing `pandoc` in `src/google_workspace_helper/exporter.py`
- [X] T011 [US2] Add temporary PPTX cleanup handler on success in `src/google_workspace_helper/exporter.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [X] T012 [P] Update unit tests to integrate logging configuration checks in `tests/test_logging_config.py`
- [X] T013 Run pre-commit code formatting and quality linter gates
- [X] T014 Run `quickstart.md` validation scenario checks to verify final correctness

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
  - User stories can then proceed in parallel (if staffed) or sequentially in priority order (P1 → P2).
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable.

### Within Each User Story

- Tests MUST be written and fail before implementation (TDD).
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- Setup tasks and unit tests marked [P] can run in parallel.
- Once Foundational phase completes, User Story 1 and User Story 2 can be developed in parallel by separate developers.

---

## Parallel Example: User Story 1

```bash
# Launch test and implementation frameworks for User Story 1:
Task: "Create unit tests for CSV-to-Markdown table parsing and formatting in tests/test_postprocessor.py"
Task: "Implement custom CSV parsing and Markdown table generation in src/google_workspace_helper/postprocessor.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready.
2. Add User Story 1 → Test independently → Deploy/Demo (Spreadsheets working!).
3. Add User Story 2 → Test independently → Deploy/Demo (Presentations working!).
4. Run final Polish and cross-cutting validation.
