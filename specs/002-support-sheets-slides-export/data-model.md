# Data Model: Support Spreadsheet and Presentation Export

## 1. Entities

### GoogleDriveFile
Represents a file to be processed from Google Drive.

- **file_id** (`str`): Standard Google Drive unique alphanumeric file identifier.
- **mime_type** (`str`): The Google Drive MimeType metadata of the file (e.g. `application/vnd.google-apps.document`, `application/vnd.google-apps.spreadsheet`, `application/vnd.google-apps.presentation`).
- **export_format** (`str`): The derived intermediate export format (e.g. `text/markdown`, `text/csv`, `application/vnd.openxmlformats-officedocument.presentationml.presentation`).

---

### ExportJobContext
Captures state and execution attributes for an ongoing export process.

- **file_id** (`str`): Unique file ID.
- **output_path** (`Path`): Destination path of the final `.md` file.
- **temp_dir** (`Path`): Local directory path where temporary intermediate files (CSV, PPTX) are handled.
- **is_presentation** (`bool`): True if presentation file detected, otherwise False.
- **is_spreadsheet** (`bool`): True if spreadsheet file detected, otherwise False.

---

## 2. Validation & Verification Rules

1. **File ID Sanitization**: File ID must contain only alphanumeric characters, dashes, or underscores to prevent shell injection or directory traversal.
2. **Pandoc Verification**: Before executing presentation conversion, `pandoc` binary availability is checked via `shutil.which("pandoc")`.
3. **MimeType Detection**: The application queries the file's MimeType using `gws drive files get` with parameter parsing, validating that the file exists and is accessible.

---

## 3. Export Process States

```text
[IDLE] ───► [METADATA_FETCH] ───► [EXPORT_STAGE] ───► [POST_PROCESS_STAGE] ───► [SUCCESS]
                                         │
                                   (gws failure / pandoc missing)
                                         ▼
                                     [FAILED]
```
