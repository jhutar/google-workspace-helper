# Feature Specification: Manage Google Tasks in Default Task List

**Feature Branch**: `004-support-google-tasks`

**Created**: 2026-10-12

**Status**: Draft

**Input**: User wants to manage tasks in their default Google Tasks list (https://tasks.google.com/tasks/) from the CLI: add tasks, list them, inspect a single task, mark tasks done by exact title, and update a task's title, details, and due date.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add a Task (Priority: P1)

Users can create a task in their default task list with a title, optional details (notes, newlines supported), and an optional due date.

**Why this priority**: Simplest write operation; core building block for all other flows.

**Independent Test**: Run `task add --title "Buy milk" --details "2 liters" --due 2026-10-20` and verify the task appears in the default list in the Tasks web UI with the given title, notes, and due date.

**Acceptance Scenarios**:

1. **Given** a title only, **When** `task add --title "Buy milk"` runs, **Then** a task with that title, no notes, and no due date is created in the default list.
2. **Given** `--details` with embedded newlines, **When** `task add` runs, **Then** the notes field preserves the newlines.
3. **Given** `--due 2026-10-20`, **When** `task add` runs, **Then** the task is due on 2026-10-20 (date only, time discarded by the API).
4. **Given** `--due 3d`, **When** `task add` runs, **Then** the due date is three days from today.
5. **Given** an invalid due format (e.g. `20-10-2026`, `tomorrow`), **When** `task add` runs, **Then** the command fails with a clear error and no task is created.
6. **Given** a missing `--title`, **When** `task add` runs, **Then** the command fails with a clear error.

---

### User Story 2 - List Tasks (Priority: P1)

Users can list tasks in their default list to discover task IDs. Open (not completed) tasks are shown by default; `--all` includes completed ones.

**Why this priority**: Task IDs are opaque; without a listing command the user cannot operate on existing tasks.

**Independent Test**: Run `task list` and verify every open task in the default list appears with its ID, title, and due date.

**Acceptance Scenarios**:

1. **Given** open and completed tasks exist, **When** `task list` runs, **Then** only open tasks are listed, each showing ID, title, and due date (if set).
2. **Given** completed tasks exist, **When** `task list --all` runs, **Then** completed tasks are also listed, marked as completed.
3. **Given** an empty task list, **When** `task list` runs, **Then** the command succeeds and prints a clear "no tasks" message.

---

### User Story 3 - Show a Task (Priority: P1)

Users can display a single task's full details: ID, title, due date, status, and notes.

**Why this priority**: Needed to read details and confirm updates.

**Independent Test**: Run `task show <task_id>` on a task with notes and a due date and verify all fields are printed.

**Acceptance Scenarios**:

1. **Given** a valid task ID, **When** `task show <id>` runs, **Then** ID, title, due date, status, and notes are printed.
2. **Given** an invalid or inaccessible task ID, **When** `task show <id>` runs, **Then** the command fails with a clear error.

---

### User Story 4 - Mark a Task Done by Exact Title (Priority: P1)

Users can mark a task as completed by providing its exact title. If no open task or multiple open tasks share the title, the command fails.

**Why this priority**: Primary completion flow; title is more ergonomic than the opaque task ID.

**Independent Test**: Run `task done "Buy milk"` and verify the task shows as completed in the Tasks web UI.

**Acceptance Scenarios**:

1. **Given** exactly one open task titled "Buy milk", **When** `task done "Buy milk"` runs, **Then** that task is marked completed and the command succeeds.
2. **Given** no open task with that title, **When** `task done "Buy milk"` runs, **Then** the command fails with a clear error and nothing is modified.
3. **Given** two open tasks with the same title, **When** `task done "Buy milk"` runs, **Then** the command fails with an error mentioning the ambiguity and nothing is modified.
4. **Given** a completed task with that title and no open one, **When** `task done "Buy milk"` runs, **Then** the command fails (completed tasks are not matched).

---

### User Story 5 - Update a Task (Priority: P1)

Users can update a task's title, details, and due date by task ID. Only the provided fields are changed.

**Why this priority**: Needed to correct or enrich existing tasks.

**Independent Test**: Run `task update <id> --due 2026-10-25` on a task and verify only the due date changed.

**Acceptance Scenarios**:

1. **Given** a valid task ID and `--due 3d`, **When** `task update` runs, **Then** only the due date changes (relative dates accepted, same as add).
2. **Given** a valid task ID and `--title`/`--details`, **When** `task update` runs, **Then** only the provided fields change.
3. **Given** no update flags, **When** `task update <id>` runs, **Then** the command fails with a clear error.
4. **Given** an invalid task ID, **When** `task update` runs, **Then** the command fails with a clear error.

---

### Edge Cases

1. **Default task list resolution**: The default list is the first list returned by `tasklists list`; if the user has no lists, the command fails with a clear error.
2. **Due date formats**: Only `YYYY-MM-DD` and relative `Nd` (days from today) are accepted; anything else fails fast with an error listing accepted formats.
3. **Un-done / reopen**: Out of scope; user can reopen in the Tasks UI.
4. **Task deletion**: Out of scope.
5. **Non-default task lists**: Out of scope; all commands operate on the default list only.
