# Feature Specification: Export Spreadsheets and Slides to Markdown

**Feature Branch**: `002-support-sheets-slides-export`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Now I realized spreadsheets and presentations can not be exported to markdown :( It says `error[api]: The requested conversion is not supported.`. So we need to find way around it. We will check before export file props and if it is spreadsheet, we will export as CSV and convert to markdown in postprocess. Unfortunatelly this only export first sheet I believe, so we need to document it if it is not possible to solve it easilly. For presentation we will export to pptx or some other format and then use Pandoc locally to convert to Markdown. Pandoc will not be a direct dependency. If it is not installed and user tries to export slides, just throw an error. I do not care too much about images/graphs. Code needs to remain nicely structured and maintainable, no huge files."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export Google Spreadsheet to Markdown Table (Priority: P1)

Users can export a Google Spreadsheet file using its file ID or URL to a clean Markdown file. Since the Google Drive API does not directly support Spreadsheet-to-Markdown conversion, the application detects the spreadsheet type, exports it as CSV, and converts the CSV data into a Markdown table during post-processing.

**Why this priority**: Essential to address the Google API limitation for spreadsheets, enabling users to consume their spreadsheet data as Markdown.

**Independent Test**: Execute the exporter on a valid Google Spreadsheet ID. Verify that the file is exported successfully as a CSV, the CSV is parsed into a clean Markdown table format, and saved to the target file path.

**Acceptance Scenarios**:

1. **Given** a valid Google Spreadsheet ID or URL, **When** the exporter command is executed, **Then** the application checks the file type, exports it as CSV, and parses it into a valid Markdown table.
2. **Given** a Google Spreadsheet with multiple sheets, **When** the exporter command is executed, **Then** the application exports only the first sheet and issues a warning alerting the user about this limitation.

---

### User Story 2 - Export Google Presentation/Slides to Markdown via Pandoc (Priority: P1)

Users can export a Google Presentation (Slides) using its file ID or URL to a clean Markdown file. Since Google Drive does not support Presentation-to-Markdown directly, the application detects the presentation type, exports it as a PPTX file, and uses local `pandoc` to convert the PPTX content into Markdown.

**Why this priority**: Crucial workaround to convert Slides content into structured text that AI agents can consume.

**Independent Test**: On a system with `pandoc` installed, export a valid Slides presentation. Verify that a PPTX file is downloaded and successfully converted into Markdown slides.

**Acceptance Scenarios**:

1. **Given** a valid Google Presentation ID or URL and a system with `pandoc` installed, **When** the exporter command is executed, **Then** the application downloads the presentation in PPTX format, invokes `pandoc` locally to convert it, and saves the clean Markdown slides.
2. **Given** a Google Presentation ID or URL and a system where `pandoc` is NOT installed, **When** the exporter command is executed, **Then** the application fails fast, terminates immediately, and outputs a clear error instructing the user to install `pandoc`.

---

### Edge Cases

- **Missing Pandoc for slides**: A user tries to export slides but `pandoc` is missing. The system fails immediately with a descriptive warning.
- **Malformed CSV input**: The exported CSV data contains empty cells, weird quotation marks, or commas. The post-processor handles parsing issues gracefully to output a valid Markdown table structure.
- **Empty Spreadsheet/Presentation**: The target Google Spreadsheet or Presentation has no content. The exporter generates a valid but empty Markdown table or minimal slide file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST retrieve file metadata (such as mimeType) before executing an export to identify the file type (Document, Spreadsheet, or Presentation).
- **FR-002**: System MUST export Google Spreadsheets to CSV format if a spreadsheet type is detected.
- **FR-003**: System MUST convert the exported CSV data to a valid Markdown table representation in the post-processing phase.
- **FR-004**: System MUST document and log a warning that only the first sheet of a multi-sheet spreadsheet will be exported.
- **FR-005**: System MUST export Google Presentations to PPTX format if a presentation type is detected.
- **FR-006**: System MUST verify if `pandoc` is installed and available in the system path before attempting to convert a presentation PPTX file.
- **FR-007**: System MUST fail fast and raise a user-friendly `FileNotFoundError` or custom error if a user attempts to export slides but `pandoc` is not installed.
- **FR-008**: System MUST execute local `pandoc` to convert the exported PPTX presentation file to Markdown slides.
- **FR-009**: Codebase structure MUST remain modular, maintainable, and cleanly separated across dedicated helper modules instead of bloated files.

### Key Entities

- **Google Drive File**: Represents the file to be exported, defined by a unique ID and containing file properties (such as mimeType/type).
- **Export Process Context**: Captures the intermediate states (e.g., download paths, system executables) and post-processing conversions (CSV-to-Markdown, PPTX-to-Markdown).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Exporting a Google Spreadsheet successfully converts the first sheet to a Markdown table in less than 5 seconds.
- **SC-002**: Exporting a Google Presentation on a system with `pandoc` successfully generates Markdown slide content.
- **SC-003**: Exporting a Google Presentation on a system without `pandoc` fails fast in less than 2 seconds, displaying a descriptive installation instruction.

## Assumptions

- Users have `gws` installed and authenticated.
- For Presentation export, the system relies on the user's local host having `pandoc` installed. `pandoc` is not packaged as a direct python dependency.
- Spreadsheet formatting (colors, formulas, borders, merged cells) is out of scope.
- Images and graphs within spreadsheets and presentations are secondary and do not need to be extracted or processed.
