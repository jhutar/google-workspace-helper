# CLI Contract: Spreadsheet and Presentation Export Support

## 1. Command Syntax
The tool is executed as a Python CLI script supporting subcommands.

```bash
google-workspace-helper <subcommand> [arguments] [options]
```

## 2. Subcommands

### `export`
Exports a Google Drive document, spreadsheet, or slide file (and URLs) to Markdown, cleaning inline base64 images, converting spreadsheets to tables, and slide files to markdown sections.

```bash
google-workspace-helper export <file_id_or_url> [--output OUTPUT_PATH]
```

#### Arguments
- `file_id_or_url` (Position, Required): Valid alphanumeric Google Drive file identifier or standard document/spreadsheet/presentation sharing URL.

#### Options
- `-o`, `--output` (Optional): The file path where the resulting clean markdown should be saved. If omitted, the file is saved in the current working directory as `<file_id>.md`.

---

## 3. Exit Codes
- `0`: Success. Export complete, clean Markdown table/slides generated and successfully saved.
- `1`: Validation, runtime, or logic failure (e.g. invalid file ID, missing `pandoc` binary for presentation export, write permission denied).
- `2`: Command syntax error (argparse built-in).

---

## 4. Standard Output and Error
- **Stdout**: On success, the tool outputs the final saved markdown file path.
- **Stderr**: Surfaced warning alerts (such as the multi-sheet spreadsheet limitations) and execution errors.
