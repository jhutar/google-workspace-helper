# Feature Specification: Google Drive Markdown Exporter

**Feature Branch**: `001-export-gdrive-markdown`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "To give AI agent simple access to my documents in Google Drive, I want to build an app that allows to export any document (for now document, spreadsheet and slides) to markdown file. If the document contains images they are present as base64 data, so the tool needs to post-process the md file and move images to \"/tmp/<doc_id>/\" directory and refer them properly from the doc. I want the document to be clean and consumable by AI aget at the end. This is just a thin wrapper around `gws` CLI tool, mostly just using it's `gws drive files export --params '{\"fileId\": \"1qXUszdKD2ytd7vkl1wup6d32ATb_Rl4IH0_xeOxceXo\", \"mimeType\": \"text/markdown\"}'` function."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export Google Doc to Markdown (Priority: P1)

Users can export standard Google Documents (text documents) to a clean markdown file using a file ID.

**Why this priority**: Core MVP requirement. Without standard document export capability, the tool cannot deliver its primary value of making text document content accessible to AI agents.

**Independent Test**: Execute the exporter with a valid Google Doc ID containing only text. Verify that `gws` is called, a markdown file is created, and the content matches the original text structure without corruptions.

**Acceptance Scenarios**:

1. **Given** a valid Google Doc file ID and a target output path, **When** the exporter command is executed, **Then** the application exports the document to markdown using `gws` and saves the clean markdown file at the target output path.
2. **Given** an invalid or inaccessible Google Doc file ID, **When** the exporter command is executed, **Then** the application fails fast, terminates execution immediately, and displays a descriptive, user-friendly error message.

---

### User Story 2 - Extract and Post-Process Embedded Images (Priority: P1)

When an exported document contains embedded images (represented as base64 URIs), the system automatically extracts them, decodes them to a local directory, and rewrites the markdown to reference the local files.

**Why this priority**: Essential for keeping markdown files clean, lightweight, and highly consumable for AI agents, which struggle with or waste tokens on large base64 image strings.

**Independent Test**: Export a Google Document that contains embedded images. Verify that the output markdown contains no inline base64 content, a directory named `/tmp/<doc_id>/` is created containing the decoded image files (e.g., JPEG/PNG), and the image links in the markdown point correctly to `/tmp/<doc_id>/image_[index].[ext]`.

**Acceptance Scenarios**:

1. **Given** an exported document containing multiple inline base64 images, **When** the post-processor runs, **Then** it creates the directory `/tmp/<doc_id>/` (if it does not exist), decodes and saves each image as a separate binary file (e.g., `/tmp/<doc_id>/image_1.png`), and replaces the base64 URI strings with standard relative markdown links `![image](/tmp/<doc_id>/image_1.png)`.
2. **Given** an exported document containing an invalid or corrupt base64 image string, **When** the post-processor runs, **Then** the system fails fast, reports the decoding failure explicitly, and prevents saving a corrupted markdown file.

---

### User Story 3 - Export Google Spreadsheets and Slides (Priority: P2)

Users can export Google Spreadsheets and Google Slides presentations to clean markdown, with all embedded images extracted and post-processed in the exact same manner as Documents.

**Why this priority**: Expands the utility of the tool to cover other common corporate document types that AI agents need to consume.

**Independent Test**: Export a Google Spreadsheet with embedded charts/images and a Google Slides file. Verify that they are exported successfully to markdown tables and slides text sections, and any embedded images are cleanly moved to `/tmp/<doc_id>/` with correct markdown references.

**Acceptance Scenarios**:

1. **Given** a valid Google Spreadsheet or Google Slides file ID, **When** the exporter command is executed, **Then** the system exports the content into clean markdown layout (using tables for spreadsheets and structured headings for slides) and decodes all embedded images into `/tmp/<doc_id>/`.

---

### Edge Cases

- **Large Documents/Images**: A document with dozens of high-resolution images might exceed memory during base64 processing. The tool must stream or process images sequentially to avoid Out-Of-Memory (OOM) exceptions.
- **Duplicate Doc IDs / Multi-Run Overwrites**: Running the export multiple times for the same `<doc_id>` must safely overwrite or refresh `/tmp/<doc_id>/` without duplicate files or write permission conflicts.
- **Varying Image Formats**: Embedded images can be PNG, JPEG, GIF, SVG, etc. The decoder must parse the base64 MIME-type prefix (e.g. `data:image/png;base64,...`) and apply the correct file extension dynamically.
- **Incomplete/Interrupted Exports**: If the connection drops or `gws` fails mid-process, the tool must not write a partially processed markdown file or leave orphan image files in `/tmp/`. It must clean up temporary states and fail fast.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept a Google Drive file ID as a required command-line argument.
- **FR-002**: The system MUST support an optional output directory argument, defaulting to the current directory if not specified.
- **FR-003**: The system MUST use the `gws` CLI tool via subprocess execution to export the Google Drive file to text/markdown format.
- **FR-004**: The system MUST parse the exported markdown and identify all inline base64 image strings matching the pattern `data:image/<mime>;base64,<data>`.
- **FR-005**: The system MUST create a local directory at `/tmp/<doc_id>/` where `<doc_id>` is the provided Google Drive file ID.
- **FR-006**: For each identified base64 image, the system MUST decode the base64 data to binary and save it to `/tmp/<doc_id>/image_<index>.<extension>`, where index is 1-based and extension is derived from the MIME-type.
- **FR-007**: The system MUST replace the inline base64 string in the markdown with clean relative references pointing to the local files (e.g., `![image](/tmp/<doc_id>/image_<index>.<extension>)`).
- **FR-008**: The system MUST validate that the `gws` CLI tool is installed and accessible in the system PATH before running any exports, failing fast if not found.
- **FR-009**: The system MUST handle execution errors from `gws` explicitly, raising a clear exception and terminating immediately.

### Key Entities

- **ExportJob**: Manages the lifecycle of a single export execution.
  - Attributes: `file_id` (string), `output_path` (string), `temp_image_dir` (string), `status` (enum: PENDING, EXPORTING, POST_PROCESSING, SUCCESS, FAILED).
- **DocumentContent**: Represents the loaded markdown text and its structure.
  - Attributes: `raw_markdown` (string), `clean_markdown` (string), `detected_images` (list of ExtractedImage).
- **ExtractedImage**: Represents an embedded image found in the document.
  - Attributes: `index` (integer), `mime_type` (string), `extension` (string), `base64_data` (string), `local_path` (string).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Standard text documents (without images) are exported to clean markdown in under 5 seconds.
- **SC-002**: Resulting processed markdown files contain exactly 0% inline base64 data (100% of images are successfully extracted and replaced with local references).
- **SC-003**: Extracted image files are fully readable and identical in binary hash to the original embedded source.
- **SC-004**: The system fails fast and terminates within 500ms if input file ID is empty, invalid, or inaccessible.

## Assumptions

- The `gws` CLI tool is pre-installed on the host system, authenticated with appropriate Google Drive credentials, and has network access to Google Drive API.
- The directory `/tmp/` is writeable by the active system user executing the tool.
- Google Drive file IDs are alphanumeric and do not contain special characters that could compromise shell command construction.
- Markdown structure exported by `gws` follows standard CommonMark or GitHub Flavored Markdown (GFM) formats.
