# Data Model: Google Drive Markdown Exporter

## Core Entities

### 1. ExportJob (In-Memory Process State)
Manages the lifecycle and state of a single document export task.

| Field | Type | Description |
|---|---|---|
| `file_id` | `str` | Required Google Drive file identifier. |
| `output_path` | `str` | Destination markdown file path. |
| `temp_image_dir` | `str` | Image directory path: `/tmp/<file_id>/`. |
| `status` | `str` | Enum: `PENDING`, `EXPORTING`, `POST_PROCESSING`, `SUCCESS`, `FAILED`. |
| `error_message` | `Optional[str]` | Populated on failure state. |

#### State Transitions
```text
  [PENDING]
      │
      ▼
 [EXPORTING] ───(gws failure)───► [FAILED]
      │
      ▼
[POST_PROCESSING] ─(decode error)─► [FAILED]
      │
      ▼
  [SUCCESS]
```

### 2. DocumentContent
Represents the loaded and processed markdown content.

| Field | Type | Description |
|---|---|---|
| `raw_markdown` | `str` | Original markdown exported by `gws` containing base64 images. |
| `clean_markdown` | `str` | Processed markdown with base64 URIs replaced by relative paths. |
| `detected_images` | `List[ExtractedImage]` | List of all extracted image metadata. |

### 3. ExtractedImage
Represents a parsed inline base64 image ready for extraction.

| Field | Type | Description |
|---|---|---|
| `index` | `int` | 1-based index representing image order in document. |
| `mime_type` | `str` | Parsed MIME-type (e.g. `image/png`, `image/jpeg`). |
| `extension` | `str` | Dynamic file extension derived from MIME-type (`png`, `jpg`, etc.). |
| `base64_data` | `str` | Raw base64 encoded payload bytes string. |
| `local_path` | `str` | Final destination path: `/tmp/<file_id>/image_<index>.<extension>`. |

## Validation Rules
1. **File ID**: Alphanumeric string, must not be empty. Must not contain shell escape characters.
2. **MIME-type Parsing**: Pattern `data:image/(?P<mime>[a-zA-Z0-9+-.]+);base64,(?P<data>[a-zA-Z0-9+/= \r\n]+)` must match; non-image MIME-types must be rejected.
3. **Write Access**: Target output path and `/tmp/<file_id>/` must be verified writeable before processing.
