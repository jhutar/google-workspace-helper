# Feature Specification: Append Text and Images to Google Documents

**Feature Branch**: `003-support-appending-to-docs`

**Created**: 2026-06-29

**Status**: Draft

**Input**: User wants to append locally stored graphs (PNG images) with descriptive text to the end of an existing Google Document report. This is the first write-path feature for the tool, complementing the existing read-only export functionality.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Append Text to a Google Document (Priority: P1)

Users can append plain text (including multi-line) to the end of an existing Google Document. The text is inserted as a new paragraph, separated from existing content.

**Why this priority**: Simplest building block of the feature; text-only append is needed independently and as part of the combined text+image flow.

**Independent Test**: Execute the append command with `--text` on a valid Google Document ID. Verify that the text appears at the end of the document as a new paragraph.

**Acceptance Scenarios**:

1. **Given** a valid Google Document ID and `--text "Some description"`, **When** the append command is executed, **Then** the text is inserted at the end of the document body as a new paragraph.
2. **Given** a valid Google Document ID and `--text` containing newlines, **When** the append command is executed, **Then** each newline produces a separate paragraph in the document.
3. **Given** an invalid or inaccessible Document ID, **When** the append command is executed, **Then** the command fails with a clear error message.

---

### User Story 2 - Append an Image to a Google Document (Priority: P1)

Users can append a local image file (PNG, JPEG, or GIF) to the end of an existing Google Document. The image is uploaded to Google Drive temporarily, inserted into the document, and the temporary Drive file is deleted afterward.

**Why this priority**: Core use case — adding locally generated graphs to reports.

**Independent Test**: Execute the append command with `--image path/to/graph.png` on a valid Google Document ID. Verify that the image appears at the end of the document and no orphaned files remain in Google Drive.

**Acceptance Scenarios**:

1. **Given** a valid Document ID and `--image graph.png`, **When** the append command is executed, **Then** the image is uploaded to Drive, inserted at the end of the document, and the temporary Drive file is deleted.
2. **Given** an image insertion that fails (API error), **When** the error occurs, **Then** the temporarily uploaded Drive file is still deleted (cleanup via `try/finally`) and the error is raised to the user.
3. **Given** a cleanup/delete that fails after successful insertion, **When** the delete error occurs, **Then** the error is raised to the user (errors are never masked).

---

### User Story 3 - Append Text and Image Together (Priority: P1)

Users can provide both `--text` and `--image` in a single command. Text is inserted first, then the image below it. The final document reads: `...existing content... [text] [image]`.

**Why this priority**: Primary use case — adding a graph with its description in one operation.

**Independent Test**: Execute the append command with both `--text` and `--image`. Verify ordering in the document matches: existing content, then text paragraph, then image.

**Acceptance Scenarios**:

1. **Given** both `--text "Graph description"` and `--image graph.png`, **When** the append command is executed, **Then** the document ends with the text paragraph followed by the image.
2. **Given** both flags provided, **When** the `--help` output is consulted, **Then** it documents that text is inserted before the image.

---

### Edge Cases

- **Neither `--text` nor `--image` provided**: The CLI validates that at least one is required and exits with an error before making any API calls.
- **Image file does not exist locally**: The CLI validates the file path before attempting upload and exits with a clear error.
- **Image too large**: Files over 50 MB or exceeding 25 megapixels are rejected by the Google Docs API. The error from the API is surfaced to the user.
- **Unsupported image format**: Only PNG, JPEG, and GIF are supported by the Docs API. Other formats produce an API error surfaced to the user.
- **Non-document file ID**: If the user provides a spreadsheet or presentation ID, the command should fail with a clear error indicating that append only works with documents.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an `append` subcommand alongside the existing `export` subcommand.
- **FR-002**: System MUST accept a positional `file_id` parameter (Google Document ID or URL).
- **FR-003**: System MUST accept optional `--text` and `--image` flags, requiring at least one.
- **FR-004**: System MUST validate that the target file is a Google Document (not spreadsheet or presentation) before proceeding.
- **FR-005**: System MUST insert text at the end of the document body as a new paragraph, supporting newlines.
- **FR-006**: System MUST upload local image files to Google Drive for insertion.
- **FR-007**: System MUST set `role: "reader", type: "domain"` permissions on the uploaded image so the Docs API can fetch it.
- **FR-008**: System MUST retrieve the `webContentLink` from Drive file metadata to obtain the image URL.
- **FR-009**: System MUST insert the image into the document via the Docs `batchUpdate` API using `insertInlineImage`.
- **FR-010**: System MUST delete the temporarily uploaded Drive file in a `try/finally` block, regardless of insertion success or failure.
- **FR-011**: System MUST raise errors on any failure — insert failure, cleanup failure — and never mask them.
- **FR-012**: When both `--text` and `--image` are provided, text MUST be inserted first, image second (text appears above image in the document).
- **FR-013**: System MUST extract the shared `gws` subprocess invocation pattern into a dedicated `gws_runner.py` helper module.
- **FR-014**: System MUST refactor `exporter.py` to use the shared `gws_runner.py` helper (in a separate commit).
- **FR-015**: System MUST validate that the `gws` CLI is installed once at startup, not on every subprocess call.

### Key Entities

- **Google Document**: The target document to append content to, identified by file ID.
- **Temporary Drive File**: The uploaded image file, created and deleted within a single append operation.
- **Drive Permissions**: Short-lived domain-reader permission set on the temporary file to allow Docs API to fetch it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Appending text to a Google Document inserts it as a new paragraph at the end of the document body.
- **SC-002**: Appending an image uploads, inserts, and cleans up with no orphaned files in Drive on success.
- **SC-003**: Partial failures (insert fails) still clean up the temporary Drive file.
- **SC-004**: All error paths raise errors to the user — no silent failures.
- **SC-005**: Existing `export` functionality continues to work unchanged after the `gws_runner.py` refactor.

## Assumptions

- Users have `gws` installed and authenticated with sufficient scopes (`drive`, `docs`).
- The `role: "reader", type: "domain"` permission is sufficient for the Docs API to fetch the uploaded image. If not, this will be changed to `type: "anyone"` after testing.
- Images are PNG, JPEG, or GIF, under 50 MB, under 25 megapixels.

## Clarifications

### Grilling Session 2026-06-29

- Q: Should `append` be a peer subcommand to `export`? → A: Yes, `google-workspace-helper append <file_id> [--text] [--image]`.
- Q: Should `--image` support multiple images? → A: No, single image only.
- Q: What order when both provided? → A: Text first, then image. Documented in `--help`.
- Q: How to handle image upload cleanup on failure? → A: `try/finally` — always attempt delete. Raise all errors.
- Q: Should errors be masked? → A: Never. All errors raised.
- Q: New module or extend `exporter.py`? → A: New `appender.py` module + shared `gws_runner.py` helper.
- Q: Refactor `exporter.py` to use helper? → A: Yes, in a separate commit.
- Q: How to get the image URL for insertion? → A: Use `webContentLink` from Drive file metadata (not manually constructed URL).
- Q: What Drive permissions for the temporary upload? → A: `role: "reader", type: "domain"` — test if Docs API can fetch it.
- Q: Error type hierarchy? → A: `RuntimeError` everywhere, reconsider only if readability suffers.
- Q: Plain text or rich formatting for `--text`? → A: Plain text only. Newlines supported.
- Q: Stdin support for `--text`? → A: No.
- Q: Helper module name? → A: `gws_runner.py`.
- Q: Helper function design? → A: 4 public wrappers + 1 private subprocess function + 1 init check function.
