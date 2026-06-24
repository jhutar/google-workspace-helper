# Quickstart: Spreadsheet and Presentation Export Validation Guide

This guide describes how to run and validate the Spreadsheet-to-Markdown and Presentation-to-Markdown export functionality.

## 1. Prerequisites
- **Python**: Version 3.12+
- **Google Workspace CLI (`gws`)**: Pre-installed and authenticated on your local machine.
- **Pandoc**: Local binary installed and accessible in your system PATH (required for slides conversion).

## 2. Setup
Install the CLI tool locally in editable mode:

```bash
uv tool install -e .
```

---

## 3. Spreadsheet Export Validation Scenario

### Input
A valid Google Spreadsheet ID or sharing URL.

### Command Execution
```bash
google-workspace-helper export <spreadsheet_id_or_url> --output test_sheet.md
```

### Expected Outcome
1. **Exit Code**: `0`.
2. **Output File**: A clean `test_sheet.md` file created in the current directory, formatted as a standard Markdown table representing the first sheet of the spreadsheet.
3. **Warnings**: A warning logged to `stderr` indicating that only the first sheet was exported.
4. **Log File**: `google-workspace-helper.log` created in the current working directory containing detailed `DEBUG` trace logs.

---

## 4. Presentation/Slides Export Validation Scenario

### Input
A valid Google Slides ID or sharing URL.

### Command Execution (With Pandoc installed)
```bash
google-workspace-helper export <slides_id_or_url> --output test_slides.md
```

### Expected Outcome
1. **Exit Code**: `0`.
2. **Output File**: A clean `test_slides.md` file created in the current directory, containing Markdown slides structure converted via local `pandoc`.
3. **Cleanup**: No intermediate PPTX file left in the directory.

### Command Execution (Without Pandoc installed)
Uninstall/rename `pandoc` or clear PATH to run without `pandoc`.

```bash
google-workspace-helper export <slides_id_or_url> --output test_slides.md
```

### Expected Outcome
1. **Exit Code**: `1`.
2. **Stderr Output**: Clear error message instructing the user to install `pandoc`.
