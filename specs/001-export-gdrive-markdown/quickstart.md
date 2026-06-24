# Quickstart: Google Drive Markdown Exporter Validation Guide

This guide describes how to run and validate the end-to-end functionality of the Google Drive Markdown Exporter.

## 1. Prerequisites
- **Python**: Version 3.12+ (installed via `uv python install 3.12`).
- **Google Workspace CLI (`gws`)**: Pre-installed and authenticated on your local machine.
- **uv**: Python package manager.

## 2. Setup
Clone the repository, install development tools, and install the CLI globally in editable mode:

```bash
make bootstrap
uv tool install -e .
```

This will initialize pre-commit hooks, prepare the development workspace, and install the `google-workspace-helper` command.

## 3. Standard Export Validation Scenario

### Input
A valid Google Document ID (e.g., `1qXUszdKD2ytd7vkl1wup6d32ATb_Rl4IH0_xeOxceXo`) containing inline images.

### Command Execution
Run the following command from any directory:

```bash
google-workspace-helper export 1qXUszdKD2ytd7vkl1wup6d32ATb_Rl4IH0_xeOxceXo --output test_export.md
```

### Expected Outcome
1. **Exit Code**: `0`.
2. **Output File**: A clean `test_export.md` file created in the current directory.
3. **Images Folder**: A directory created at `/tmp/1qXUszdKD2ytd7vkl1wup6d32ATb_Rl4IH0_xeOxceXo/` containing files like `image_1.png` and `image_2.png`.
4. **Markdown Content**: The file `test_export.md` contains NO `data:image/...;base64,...` inline text. All inline images are replaced with `![image](/tmp/1qXUszdKD2ytd7vkl1wup6d32ATb_Rl4IH0_xeOxceXo/image_1.png)` links.

## 4. Run Tests & Linting
Verify quality standards and test suite passes successfully:

```bash
# Run full pytest suite
make test

# Run quality checks (ruff linter and formatter)
make check-all
```
