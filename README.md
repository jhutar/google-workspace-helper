# Google Workspace Helper

CLI utility to assist with Google Workspace operations. Currently supports exporting Google Drive files (documents, spreadsheets, and slides) to clean Markdown with local image decoding and extraction.

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
