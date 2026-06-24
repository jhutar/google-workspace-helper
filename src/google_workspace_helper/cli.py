import argparse
import sys
import re
from pathlib import Path
from google_workspace_helper.exporter import export_file
from google_workspace_helper.postprocessor import post_process_markdown


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
    """Handles the 'export' subcommand logic."""
    file_id = args.file_id
    try:
        validate_file_id(file_id)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    # Determine default output path if not specified
    output_path_str = args.output
    if not output_path_str:
        output_path_str = f"{file_id}.md"
    output_path = Path(output_path_str)

    try:
        # Step 1: Export content from Google Workspace via gws
        raw_markdown = export_file(file_id)

        # Step 2: Post-process base64 inline images
        clean_markdown = post_process_markdown(raw_markdown, file_id)

        # Step 3: Write final markdown content to output path
        output_path.write_text(clean_markdown, encoding="utf-8")

        print(f"Success: Exported clean markdown to {output_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Entry point for the CLI tool."""
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
    export_parser.add_argument("file_id", help="Google Drive file ID to export.")
    export_parser.add_argument(
        "-o",
        "--output",
        help="Optional path to save output markdown. Defaults to '<file_id>.md'.",
    )
    export_parser.set_defaults(func=handle_export)

    # Parse command line args
    args = parser.parse_args()

    # Dispatch to subcommand function
    if hasattr(args, "func"):
        return args.func(args)
    else:
        parser.print_help()
        return 2


if __name__ == "__main__":
    sys.exit(main())
