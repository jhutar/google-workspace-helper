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
from google_workspace_helper.tasks import (
    add_task,
    get_task,
    list_tasks,
    mark_task_done_by_title,
    update_task,
)


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


def _format_due(due: str | None) -> str:
    """Format an RFC 3339 due timestamp as a plain date string."""
    return due.split("T")[0] if due else "none"


def handle_task_add(args: argparse.Namespace) -> int:
    try:
        task = add_task(args.title, notes=args.details, due=args.due)
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1
    print(f"Success: Added task '{task.get('title', '')}' (ID: {task.get('id', '')})")
    return 0


def handle_task_list(args: argparse.Namespace) -> int:
    try:
        tasks = list_tasks(include_completed=args.all)
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1
    if not tasks:
        print("No tasks found.")
        return 0
    for task in tasks:
        completed = " [completed]" if task.get("status") == "completed" else ""
        print(
            f"{task.get('id', '')}  {task.get('title', '')}  "
            f"due {_format_due(task.get('due'))}{completed}"
        )
    return 0


def handle_task_show(args: argparse.Namespace) -> int:
    try:
        task = get_task(args.task_id)
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1
    print(f"ID: {task.get('id', '')}")
    print(f"Title: {task.get('title', '')}")
    print(f"Status: {task.get('status', '')}")
    print(f"Due: {_format_due(task.get('due'))}")
    print(f"Notes: {task.get('notes', '')}")
    return 0


def handle_task_done(args: argparse.Namespace) -> int:
    try:
        task = mark_task_done_by_title(args.title)
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1
    print(
        f"Success: Marked task '{task.get('title', '')}' as done (ID: {task.get('id', '')})"
    )
    return 0


def handle_task_update(args: argparse.Namespace) -> int:
    if not args.title and not args.details and not args.due:
        print(
            "Error: At least one of --title, --details or --due must be provided.",
            file=sys.stderr,
        )
        return 1
    try:
        task = update_task(
            args.task_id, title=args.title, notes=args.details, due=args.due
        )
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1
    print(f"Success: Updated task '{task.get('title', '')}' (ID: {task.get('id', '')})")
    return 0


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

    # Define 'task' subcommand group
    task_parser = subparsers.add_parser(
        "task",
        help="Manage tasks in the default Google Tasks list.",
    )
    task_subparsers = task_parser.add_subparsers(
        dest="task_command", required=True, help="Available task commands"
    )

    task_add_parser = task_subparsers.add_parser(
        "add", help="Add a task to the default task list."
    )
    task_add_parser.add_argument("--title", required=True, help="Task title.")
    task_add_parser.add_argument(
        "--details", help="Task notes/details. Newlines are supported."
    )
    task_add_parser.add_argument(
        "--due",
        help="Due date as YYYY-MM-DD or a relative format like 3d (3 days from today).",
    )
    task_add_parser.set_defaults(func=handle_task_add)

    task_list_parser = task_subparsers.add_parser(
        "list", help="List tasks in the default task list."
    )
    task_list_parser.add_argument(
        "--all", action="store_true", help="Include completed tasks."
    )
    task_list_parser.set_defaults(func=handle_task_list)

    task_show_parser = task_subparsers.add_parser(
        "show", help="Show full details of a task."
    )
    task_show_parser.add_argument("task_id", help="Task ID (see 'task list').")
    task_show_parser.set_defaults(func=handle_task_show)

    task_done_parser = task_subparsers.add_parser(
        "done", help="Mark a task as done by its exact title."
    )
    task_done_parser.add_argument(
        "title",
        help="Exact title of the open task to mark done. Must be unique among open tasks.",
    )
    task_done_parser.set_defaults(func=handle_task_done)

    task_update_parser = task_subparsers.add_parser(
        "update", help="Update a task's title, details or due date."
    )
    task_update_parser.add_argument("task_id", help="Task ID (see 'task list').")
    task_update_parser.add_argument("--title", help="New task title.")
    task_update_parser.add_argument("--details", help="New task notes/details.")
    task_update_parser.add_argument(
        "--due",
        help="New due date as YYYY-MM-DD or a relative format like 3d.",
    )
    task_update_parser.set_defaults(func=handle_task_update)

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
