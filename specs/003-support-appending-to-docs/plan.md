# Implementation Plan: Append Text and Images to Google Documents

**Branch**: `003-support-appending-to-docs` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-support-appending-to-docs/spec.md`

## Summary

Add a write-path `append` subcommand to the CLI, allowing users to add text and/or a local image to the end of an existing Google Document. This introduces:

1. **`gws_runner.py`**: Shared helper module encapsulating all `gws` CLI subprocess invocations, replacing inline subprocess boilerplate across the codebase.
2. **`appender.py`**: New module implementing the append logic — text insertion via Docs `batchUpdate`, image upload-insert-cleanup lifecycle via Drive and Docs APIs.
3. **Refactored `exporter.py`**: Migrated to use `gws_runner.py` helpers instead of inline subprocess calls.

---

## Technical Context

**Language/Version**: Python >=3.12

**Primary Dependencies**: Built-in standard libraries (`json`, `subprocess`, `shutil`, `argparse`, `pathlib`), external subprocess (`gws`).

**Testing**: `pytest` and `unittest.mock` for mocking `gws_runner` helper functions.

**Project Type**: CLI utility tool.

**Constraints**:
- No new Python dependencies.
- Temporary Drive files must always be cleaned up (`try/finally`).
- Errors are never masked — all failures raised to the user.
- The `gws_runner.py` refactor of `exporter.py` must be a separate commit from the append feature.

---

## Project Structure

### Source Code (after implementation)

```text
src/
└── google_workspace_helper/
    ├── __init__.py
    ├── cli.py            # Argument parsing — adds `append` subcommand
    ├── gws_runner.py     # NEW: shared gws subprocess helpers
    ├── exporter.py       # REFACTORED: uses gws_runner.py
    ├── appender.py       # NEW: append text/image to Google Document
    ├── postprocessor.py  # Unchanged
    └── logging_config.py # Unchanged

tests/
├── test_cli.py           # Extended with append CLI tests
├── test_gws_runner.py    # NEW: tests for shared helpers
├── test_appender.py      # NEW: tests for append logic + error paths
├── test_exporter.py      # Updated to mock gws_runner instead of subprocess
├── test_postprocessor.py # Unchanged
└── test_logging_config.py# Unchanged
```

---

## Implementation Phases

### Phase 1: Extract `gws_runner.py` and refactor `exporter.py` (separate commit)

**Goal**: Extract the shared `gws` subprocess pattern into a dedicated module and migrate `exporter.py` to use it. Zero functional change.

#### 1.1 Create `src/google_workspace_helper/gws_runner.py`

Private workhorse function:

```python
def _run_gws_subprocess(cmd: list[str]) -> subprocess.CompletedProcess:
```

Handles `subprocess.run(cmd, capture_output=True, text=True, check=True)` with error wrapping (catches `CalledProcessError`, extracts stderr, raises `RuntimeError`).

Public functions:

```python
def check_gws_installed() -> None:
    """Verify gws CLI is available. Called once at startup."""

def run_gws(*args: str) -> None:
    """Run a gws command that only needs to succeed."""

def run_gws_json(*args: str, json_body: dict | None = None) -> dict:
    """Run a gws command and return parsed JSON stdout."""

def run_gws_to_file(*args: str, output_path: Path) -> Path:
    """Run a gws command that writes output to a file."""

def run_gws_upload(*args: str, upload_path: Path, upload_content_type: str | None = None) -> dict:
    """Run a gws command with file upload, return parsed JSON response."""
```

#### 1.2 Refactor `exporter.py`

Replace all inline `subprocess.run(["gws", ...])` calls with the appropriate `gws_runner` helper function. Remove the local `shutil.which("gws")` check (now handled by `check_gws_installed()` at startup).

#### 1.3 Update `cli.py`

Call `check_gws_installed()` once at the start of command dispatch, before entering `export` or (later) `append`.

#### 1.4 Create `tests/test_gws_runner.py`

Test each public function:
- `check_gws_installed` — present and missing scenarios.
- `run_gws` — success and failure.
- `run_gws_json` — valid JSON, invalid JSON, with `json_body`.
- `run_gws_to_file` — file written, command failure.
- `run_gws_upload` — upload with/without content type, failure.

#### 1.5 Update `tests/test_exporter.py`

Change mocks from `subprocess.run` to `gws_runner` helper functions. All existing tests must continue to pass.

**Commit**: `refactor: extract gws subprocess helpers into gws_runner.py`

---

### Phase 2: Implement `append` subcommand

**Goal**: Add the `append` subcommand with text and image support.

#### 2.1 Create `src/google_workspace_helper/appender.py`

Core functions:

```python
def append_text(file_id: str, text: str) -> None:
    """Append plain text to end of document as a new paragraph."""
```

Uses `gws docs documents batchUpdate` with `insertText` + `endOfSegmentLocation`.

```python
def append_image(file_id: str, image_path: Path) -> None:
    """Upload image to Drive, insert into document, clean up."""
```

Multi-step lifecycle:
1. `run_gws_upload(...)` — upload image to Drive.
2. `run_gws_json(...)` — set `role: "reader", type: "domain"` permission.
3. `run_gws_json(...)` — get file metadata for `webContentLink`.
4. `run_gws_json(...)` — `batchUpdate` with `insertInlineImage` + `endOfSegmentLocation`.
5. In `finally`: `run_gws(...)` — delete the temporary Drive file.

```python
def append_to_document(file_id: str, text: str | None, image_path: Path | None) -> None:
    """Orchestrate append: validate doc type, insert text then image."""
```

Validates MIME type is `application/vnd.google-apps.document`. Calls `append_text` then `append_image` as needed.

#### 2.2 Extend `cli.py`

Add `append` subparser:
- Positional: `file_id` (same validation as `export`).
- Optional: `--text TEXT` — plain text to append (supports newlines).
- Optional: `--image PATH` — path to local image file (PNG/JPEG/GIF).
- Validation: at least one of `--text` or `--image` required.
- Help text documents that text is inserted before image when both provided.

#### 2.3 Create `tests/test_appender.py`

Tests mocking at `gws_runner` helper level:
- `test_append_text` — text inserted via batchUpdate.
- `test_append_image_success` — full lifecycle: upload, permissions, metadata, insert, delete.
- `test_append_image_insert_fails_cleanup_succeeds` — insert raises, delete still called, error raised.
- `test_append_image_insert_succeeds_cleanup_fails` — insert works, delete raises, error raised.
- `test_append_image_both_fail` — insert raises, delete raises, error raised (not masked).
- `test_append_both_text_and_image` — text inserted first, then image flow.
- `test_append_non_document_rejected` — spreadsheet/presentation ID rejected with clear error.
- `test_append_no_flags_rejected` — CLI validation error.

#### 2.4 Extend `tests/test_cli.py`

- Test argument parsing for `append` subcommand.
- Test validation: at least one of `--text`/`--image` required.
- Test file ID extraction from URLs works for `append` too.

**Commit**: `feat: add append subcommand to insert text and images into Google Documents`

---

## API Calls Reference

### Append Text

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{"requests": [{"insertText": {"endOfSegmentLocation": {"segmentId": ""}, "text": "\nUser text here"}}]}'
```

### Upload Image to Drive

```bash
gws drive files create \
  --upload /path/to/image.png \
  --upload-content-type image/png
```

### Set Permissions

```bash
gws drive permissions create \
  --params '{"fileId": "UPLOADED_FILE_ID"}' \
  --json '{"role": "reader", "type": "domain", "domain": "DOMAIN"}'
```

### Get File Metadata (webContentLink)

```bash
gws drive files get \
  --params '{"fileId": "UPLOADED_FILE_ID", "fields": "webContentLink"}'
```

### Insert Image into Document

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{"requests": [{"insertInlineImage": {"endOfSegmentLocation": {"segmentId": ""}, "uri": "WEB_CONTENT_LINK"}}]}'
```

### Delete Temporary File

```bash
gws drive files delete \
  --params '{"fileId": "UPLOADED_FILE_ID"}'
```

---

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| `type: "domain"` permission insufficient for Docs API to fetch image | Image insertion fails | Test manually; fallback to `type: "anyone"` is a one-line change |
| Cleanup delete fails, leaving orphaned public file | Security/clutter | Error raised to user; user can manually delete |
| Both insert and delete fail | Original error masked | Combine error messages in the raised exception |
| `webContentLink` not returned by Drive API | Image URL unavailable | Fail with clear error; investigate alternative URL construction |
| Refactoring `exporter.py` breaks existing export | Regression | Separate commit; all existing tests must pass before moving to Phase 2 |
