# Google Workspace Helper

CLI utility to assist with Google Workspace operations. Supports exporting Google Drive files (documents, spreadsheets, and slides) to clean Markdown with local image decoding and extraction, and appending text and images to Google Documents.

## Prerequisites

- Python 3.12+
- `uv` Python package manager
- `gws` CLI tool (installed and authenticated, get it <https://github.com/googleworkspace/cli>)

## Usage

Install the CLI tool locally in editable mode:
```bash
uv tool install -e .
```

This will make the `google-workspace-helper` command available globally in your path.

Export a Google Drive document, spreadsheet, or slide file to clean Markdown:
```bash
google-workspace-helper export <file_id> [-o <output_path>]
```

Append text and/or an image to a Google Document:
```bash
google-workspace-helper append <file_id> --text "Description" --image graph.png
```

Manage tasks in your default Google Tasks list:
```bash
google-workspace-helper task add --title "Buy milk" --details "2 liters" --due 3d
google-workspace-helper task list [--all]
google-workspace-helper task show <task_id>
google-workspace-helper task done "Buy milk"
google-workspace-helper task update <task_id> --title "New title" --due 2026-10-20
```
Due dates accept `YYYY-MM-DD` or a relative format like `3d` (3 days from today). `task done` matches the exact title and fails if no open task or multiple open tasks share it.

## Development

Initialize python toolchains, pre-commit hooks, and prepare the workspace:
```bash
make bootstrap
```

Run linters, code-formatters, and security checks:
```bash
make check-all
```

Run the full python test suite with pytest:
```bash
make test
```
