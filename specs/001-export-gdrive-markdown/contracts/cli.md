# CLI Contract: Google Drive Markdown Exporter

## 1. Command Syntax
The tool is executed as a Python CLI script supporting subcommands.

```bash
google-workspace-helper <subcommand> [arguments] [options]
```

## 2. Subcommands

### `export`
Exports a Google Drive document, spreadsheet, or slide file to markdown and cleans inline base64 images.

```bash
google-workspace-helper export <file_id> [--output OUTPUT_PATH]
```

#### Arguments
- `file_id` (Position, Required): Valid alphanumeric Google Drive file identifier.

#### Options
- `-o`, `--output` (Optional): The file path where the resulting clean markdown should be saved. If omitted, the file is saved in the current working directory as `<file_id>.md`.

## 3. Exit Codes
- `0`: Success. Export complete, clean markdown saved, images successfully decoded and linked locally.
- `1`: Validation or logic failure (e.g. invalid file ID, write permission denied, decoding error, missing dependencies).
- `2`: Command syntax error (argparse built-in).

## 4. Standard Output and Error
- **Stdout**: On success, the tool outputs the final saved markdown file path.
- **Stderr**: On failure, the tool outputs a clear error message starting with `Error: ` and returns exit code `1`.
