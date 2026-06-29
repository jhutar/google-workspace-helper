import argparse
import sys
import re
from pathlib import Path
from google_workspace_helper.logging_config import setup_logging
from google_workspace_helper.gws_runner import check_gws_installed
from google_workspace_helper.exporter import (
    export_file,
    get_file_mime_type,
    export_spreadsheet_as_csv,
    export_presentation_as_markdown,
    MIME_SPREADSHEET,
    MIME_PRESENTATION,
)
from google_workspace_helper.postprocessor import (
    post_process_markdown,
    csv_to_markdown_table,
)
from google_workspace_helper.appender import append_to_document


def extract_file_id(input_str: str) -> str:
    """Extracts a Google Drive file ID from a full URL if provided, otherwise returns the input string."""
    input_str = input_str.strip()
    if not input_str:
        return ""

    # Check if input looks like a URL
    if input_str.startswith(("http://", "https://")):
        # Match standard /d/<id> format
        d_match = re.search(r"/d/([a-zA-Z0-9_-]+)", input_str)
        if d_match:
            return d_match.group(1)

        # Match query parameter open?id=<id> or open?id=<id>&...
        id_match = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", input_str)
        if id_match:
            return id_match.group(1)

        raise ValueError(
            f"Error: Could not extract Google Drive File ID from URL '{input_str}'."
        )

    return input_str


def validate_file_id(file_id: str) -> None:
    """Validates that Google Drive file ID is a safe, non-empty alphanumeric string."""
    if not file_id:
        raise ValueError("Error: File ID cannot be empty.")
    # Safe regex for Google Drive IDs (alphanumeric, underscores, hyphens)
    if not re.match(r"^[a-zA-Z0-9_-]+$", file_id):
        raise ValueError(
            f"Error: Invalid File ID '{file_id}'. IDs must contain only alphanumeric characters, underscores, or hyphens."
        )


def handle_export(args: argparse.Namespace) -> int:
    raw_input = args.file_id
    try:
        file_id = extract_file_id(raw_input)
        validate_file_id(file_id)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    output_path_str = args.output

    try:
        mime_type = get_file_mime_type(file_id)

        if mime_type == MIME_SPREADSHEET:
            csv_content = export_spreadsheet_as_csv(file_id)
            clean_markdown = csv_to_markdown_table(csv_content)
        elif mime_type == MIME_PRESENTATION:
            clean_markdown = export_presentation_as_markdown(file_id)
        else:
            raw_markdown = export_file(file_id)
            clean_markdown = post_process_markdown(raw_markdown, file_id)

        if output_path_str:
            output_path = Path(output_path_str)
            output_path.write_text(clean_markdown, encoding="utf-8")
            print(f"Success: Exported clean markdown to {output_path}")
        else:
            sys.stdout.write(clean_markdown)

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def handle_append(args: argparse.Namespace) -> int:
    raw_input = args.file_id
    try:
        file_id = extract_file_id(raw_input)
        validate_file_id(file_id)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    text = args.text
    image_path = None
    if args.image:
        image_path = Path(args.image)
        if not image_path.exists():
            print(f"Error: Image file not found: {image_path}", file=sys.stderr)
            return 1

    if not text and not image_path:
        print(
            "Error: At least one of --text or --image must be provided.",
            file=sys.stderr,
        )
        return 1

    try:
        append_to_document(file_id, text=text, image_path=image_path)
        print("Success: Content appended to document.")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    setup_logging()
    parser = argparse.ArgumentParser(
        prog="google-workspace-helper",
        description="CLI utility to assist with Google Workspace operations.",
    )
    subparsers = parser.add_subparsers(
        dest="subcommand", required=True, help="Available subcommands"
    )

    # Define 'export' subcommand
    export_parser = subparsers.add_parser(
        "export", help="Export Google Drive document, spreadsheet, or slide file."
    )
    export_parser.add_argument(
        "file_id", help="Google Drive file ID or full URL to export."
    )
    export_parser.add_argument(
        "-o",
        "--output",
        help="Optional path to save output markdown. If omitted, dumps content directly to stdout.",
    )
    export_parser.set_defaults(func=handle_export)

    append_parser = subparsers.add_parser(
        "append",
        help="Append text and/or an image to a Google Document.",
    )
    append_parser.add_argument("file_id", help="Google Document file ID or full URL.")
    append_parser.add_argument(
        "--text",
        help="Plain text to append. Newlines are supported. "
        "When used with --image, text is inserted before the image.",
    )
    append_parser.add_argument(
        "--image",
        help="Path to a local image file (PNG, JPEG, or GIF) to append.",
    )
    append_parser.set_defaults(func=handle_append)

    args = parser.parse_args()

    try:
        check_gws_installed()
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1

    if hasattr(args, "func"):
        return args.func(args)
    else:
        parser.print_help()
        return 2


if __name__ == "__main__":
    sys.exit(main())
