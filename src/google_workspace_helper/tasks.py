import json
import re
from datetime import date, timedelta

from google_workspace_helper.gws_runner import run_gws_json

__all__ = [
    "get_default_tasklist_id",
    "parse_due_date",
    "list_tasks",
    "get_task",
    "add_task",
    "mark_task_done_by_title",
    "update_task",
]


def get_default_tasklist_id() -> str:
    """Return ID of the user's default task list (first list returned by the API)."""
    data = run_gws_json("tasks", "tasklists", "list")
    items = data.get("items", [])
    if not items:
        raise RuntimeError("Error: No task lists found for this account.")
    return items[0]["id"]


def parse_due_date(due: str) -> str:
    """Convert 'YYYY-MM-DD' or relative 'Nd' input to an RFC 3339 timestamp string."""
    due = due.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", due):
        parsed = date.fromisoformat(due)
    else:
        match = re.fullmatch(r"(\d+)d", due)
        if not match:
            raise ValueError(
                f"Error: Invalid due date '{due}'. "
                "Use YYYY-MM-DD or a relative format like 3d."
            )
        parsed = date.today() + timedelta(days=int(match.group(1)))
    return parsed.strftime("%Y-%m-%dT00:00:00.000Z")


def list_tasks(include_completed: bool = False) -> list[dict]:
    """Return tasks from the default task list; open tasks only unless include_completed."""
    tasklist_id = get_default_tasklist_id()
    params = json.dumps(
        {"tasklist": tasklist_id, "showCompleted": include_completed, "maxResults": 100}
    )
    data = run_gws_json("tasks", "tasks", "list", "--params", params)
    return data.get("items", [])


def get_task(task_id: str) -> dict:
    """Fetch a single task from the default task list by ID."""
    params = json.dumps(
        {"tasklist": get_default_tasklist_id(), "task": task_id}
    )
    return run_gws_json("tasks", "tasks", "get", "--params", params)


def add_task(title: str, notes: str | None = None, due: str | None = None) -> dict:
    """Create a new task in the default task list."""
    body = {"title": title}
    if notes is not None:
        body["notes"] = notes
    if due is not None:
        body["due"] = parse_due_date(due)
    params = json.dumps({"tasklist": get_default_tasklist_id()})
    return run_gws_json(
        "tasks", "tasks", "insert", "--params", params, json_body=body
    )


def mark_task_done_by_title(title: str) -> dict:
    """Mark the unique open task with exact title as completed."""
    matches = [
        t
        for t in list_tasks(include_completed=False)
        if t.get("title") == title and t.get("status") == "needsAction"
    ]
    if not matches:
        raise ValueError(f"Error: No open task found with title '{title}'.")
    if len(matches) > 1:
        raise ValueError(
            f"Error: Found {len(matches)} open tasks with title '{title}'. "
            "Titles must be unique among open tasks to mark done."
        )
    task = matches[0]
    return _patch_task(task["id"], {"status": "completed"})


def update_task(
    task_id: str,
    title: str | None = None,
    notes: str | None = None,
    due: str | None = None,
) -> dict:
    """Patch only the provided fields of a task in the default task list."""
    body = {}
    if title is not None:
        body["title"] = title
    if notes is not None:
        body["notes"] = notes
    if due is not None:
        body["due"] = parse_due_date(due)
    return _patch_task(task_id, body)


def _patch_task(task_id: str, body: dict) -> dict:
    """Send a patch request for a task in the default task list."""
    params = json.dumps({"tasklist": get_default_tasklist_id(), "task": task_id})
    return run_gws_json("tasks", "tasks", "patch", "--params", params, json_body=body)
