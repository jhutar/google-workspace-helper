# Implementation Plan: Manage Google Tasks in Default Task List

**Branch**: `004-support-google-tasks` | **Date**: 2026-10-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-support-google-tasks/spec.md`

## Summary

Add a `task` subcommand group to the CLI for managing tasks in the user's default Google Tasks list: add, list, show, done (by exact title), and update (by task ID). This introduces one new module `tasks.py` and extends `cli.py` with a nested subparser group.

---

## Technical Context

**Language/Version**: Python >=3.12

**Primary Dependencies**: Built-in standard libraries (`re`, `json`, `datetime`, `argparse`), external subprocess (`gws`).

**Testing**: `pytest` and `unittest.mock`, mocking at the `gws_runner` helper level (same pattern as `test_appender.py`).

**Constraints**:
- No new Python dependencies.
- All operations target the default task list (first item of `tasks tasklists list`).
- Only provided fields are sent in patch bodies.
- Due dates: `YYYY-MM-DD` or relative `Nd`; everything else fails fast.

---

## Project Structure

### Source Code (after implementation)

```text
src/
└── google_workspace_helper/
    ├── cli.py            # Adds `task` subcommand group (add/list/show/done/update)
    ├── tasks.py          # NEW: Google Tasks logic on top of gws_runner
    └── ...               # Unchanged

tests/
├── test_tasks.py         # NEW: tests for tasks logic + error paths
└── test_cli.py           # Extended with task CLI tests
```

---

## Implementation Phases

### Phase 1: Create `src/google_workspace_helper/tasks.py`

Core functions:

```python
def get_default_tasklist_id() -> str:
    """Return ID of first task list (the user's default list)."""

def parse_due_date(due: str) -> str:
    """Convert 'YYYY-MM-DD' or relative 'Nd' input to RFC 3339 timestamp string."""

def list_tasks(include_completed: bool = False) -> list[dict]:
    """Return tasks from the default list (open tasks by default)."""

def get_task(task_id: str) -> dict:
    """Fetch a single task from the default list."""

def add_task(title: str, notes: str | None = None, due: str | None = None) -> dict:
    """Create a task in the default list."""

def mark_task_done_by_title(title: str) -> dict:
    """Mark the unique open task with exact title as completed."""

def update_task(task_id: str, title: str | None, notes: str | None, due: str | None) -> dict:
    """Patch only the provided fields of a task."""
```

`mark_task_done_by_title` lists open tasks, matches exact title + `status == "needsAction"`:
- 0 matches -> `ValueError` (nothing modified)
- >1 matches -> `ValueError` listing the ambiguity (nothing modified)
- exactly 1 -> `tasks tasks patch` with `{"status": "completed"}`

`parse_due_date` accepts `^\d{4}-\d{2}-\d{2}$` and `^\d+d$`, returns `YYYY-MM-DDT00:00:00.000Z` (API discards time portion).

### Phase 2: Extend `cli.py`

Nested subcommand group:

```text
google-workspace-helper task add    --title T [--details D] [--due DATE]
google-workspace-helper task list   [--all]
google-workspace-helper task show   <task_id>
google-workspace-helper task done   <title>
google-workspace-helper task update <task_id> [--title T] [--details D] [--due DATE]
```

Handlers follow existing style (`handle_task_*` functions, `set_defaults(func=...)`):
- `add`: requires `--title`; prints success with new task ID.
- `list`: prints `ID  TITLE  due <date> [completed]` per line; "no tasks" message when empty.
- `show`: prints ID, title, due date (date part only), status, notes.
- `done`: requires title; prints matched task ID on success.
- `update`: requires at least one of `--title`/`--details`/`--due`.

### Phase 3: Tests

`tests/test_tasks.py` (mock `run_gws_json` at module level):
- `get_default_tasklist_id` — first list returned; empty lists raise.
- `parse_due_date` — ISO date, relative `3d`, invalid formats raise.
- `list_tasks` — open-only filtering, `--all`, empty result.
- `add_task` — body contains only provided fields; due converted to RFC 3339.
- `mark_task_done_by_title` — unique match patches status; zero matches raise; multiple matches raise.
- `update_task` — only provided fields in body; no fields handled by CLI layer.
- `get_task` — params include task and tasklist IDs.

`tests/test_cli.py`:
- Argument parsing/validation for each `task` subcommand.
- `add` without `--title` fails; `update` without any field flag fails.
- Handler error paths print to stderr and return 1.

**Commit**: `feat: add task subcommand group for Google Tasks management`

---

## API Calls Reference

### List Task Lists (default list discovery)

```bash
gws tasks tasklists list
```

### List Tasks

```bash
gws tasks tasks list --params '{"tasklist": "LIST_ID", "showCompleted": false, "maxResults": 100}'
```

### Get Task

```bash
gws tasks tasks get --params '{"tasklist": "LIST_ID", "task": "TASK_ID"}'
```

### Add Task

```bash
gws tasks tasks insert --params '{"tasklist": "LIST_ID"}' \
  --json '{"title": "Buy milk", "notes": "2 liters", "due": "2026-10-20T00:00:00.000Z"}'
```

### Patch Task (update fields or mark done)

```bash
gws tasks tasks patch --params '{"tasklist": "LIST_ID", "task": "TASK_ID"}' \
  --json '{"status": "completed"}'
```

---

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| First item of `tasklists list` is not the user's "default" list in UI sense | Tasks land in unexpected list | Tasks API has no explicit "default" flag; first list is the conventional default. Document in help text. |
| `done` by title with completed tasks sharing the title | Wrong task completed | Only open (`needsAction`) tasks are matched; ambiguity and no-match fail loudly. |
| Relative date interpretation off by timezone | Due date lands on wrong day | Local date used, API stores date only; discrepancy limited to late-night edge cases. |
| `maxResults` 100 cap hides tasks | `done` misses a matching task | Documented limitation; acceptable for current scale (single user). |
