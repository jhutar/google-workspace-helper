# Research Document: Support Spreadsheet and Presentation Export

## 1. Custom CSV to Markdown Table Conversion

### Decision
Implement a custom Python function to parse CSV files and format them directly as standard Markdown tables.

### Rationale
- **No Third-Party Dependencies**: Avoids adding complex external libraries like `pandas` or `tabulate` to keep the project lightweight.
- **Handling Formatting Nuances**: Custom code lets us explicitly sanitize table delimiters, escape pipe characters (`|`) in CSV cells, and format column headers precisely.
- **Simplicity**: CSV format parsing is straightforward using Python's built-in `csv` reader.

### Alternatives Considered
- **tabulate**: Rejected because we want to preserve the lightweight nature of this tool and avoid adding non-core dependencies to `pyproject.toml`.
- **pandas**: Excessively heavy for a simple CSV to Markdown table conversion.

---

## 2. Local Pandoc Invocation for Presentation (Slides) Conversion

### Decision
Execute local `pandoc` as an external subprocess to convert downloaded PPTX files into Markdown slides.

### Rationale
- **Industry Standard**: Pandoc is the standard tool for document conversion and supports slide formats natively.
- **No Direct Dependency**: Pandoc will be executed via Python's standard `subprocess` library. If `pandoc` is missing from the system PATH, a descriptive `FileNotFoundError` is raised immediately.
- **Robust formatting**: Converts PPTX slides into cleanly formatted markdown headings and paragraphs.

### Alternatives Considered
- **python-pptx library**: Rejected because extracting text manually and structuring it into coherent Markdown slides is highly complex, whereas Pandoc performs this layout conversion beautifully out-of-the-box.

---

## 3. Application Logging Configuration

### Decision
Utilize Python's standard `logging` library. Configure logging at application startup:
1. **File Handler**: Appends detailed logs with `DEBUG` verbosity to a local log file named `google-workspace-helper.log` on every execution.
2. **Stream Handler**: Outputs warnings, errors, and severe messages (defaults to `WARNING` level) to `stderr` with a clean, user-friendly format.

### Rationale
- **Traceability**: The `DEBUG` level log file provides rich context for troubleshooting (e.g., raw subprocess arguments, file IDs, file types, and temp folder operations).
- **User Experience**: Emitting only warnings or errors (customizable) to `stderr` keeps terminal output clean and noise-free for non-technical users.

### Alternatives Considered
- **print statement debugging**: Rejected as it does not scale and makes custom stream verbosities or file logging difficult to manage cleanly.
