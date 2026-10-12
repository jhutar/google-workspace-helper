import pytest
from unittest.mock import patch

from google_workspace_helper.tasks import (
    get_default_tasklist_id,
    parse_due_date,
    list_tasks,
    get_task,
    add_task,
    mark_task_done_by_title,
    update_task,
)

MODULE = "google_workspace_helper.tasks"

TASKLIST_ID = "MTIzNDU2Nzg5"


def _task(id, title, status="needsAction", due=None, notes=None):
    return {"id": id, "title": title, "status": status, "due": due, "notes": notes}


def test_get_default_tasklist_id():
    with patch(f"{MODULE}.run_gws_json") as mock_json:
        mock_json.return_value = {"items": [{"id": TASKLIST_ID, "title": "My List"}]}
        assert get_default_tasklist_id() == TASKLIST_ID
        mock_json.assert_called_once_with("tasks", "tasklists", "list")


def test_get_default_tasklist_id_empty():
    with patch(f"{MODULE}.run_gws_json") as mock_json:
        mock_json.return_value = {"items": []}
        with pytest.raises(RuntimeError, match="No task lists found"):
            get_default_tasklist_id()


def test_parse_due_date_iso():
    assert parse_due_date("2026-10-20") == "2026-10-20T00:00:00.000Z"


def test_parse_due_date_relative():
    from datetime import date

    with patch(f"{MODULE}.date") as mock_date:
        mock_date.today.return_value = date(2026, 10, 12)
        mock_date.side_effect = date
        assert parse_due_date("3d") == "2026-10-15T00:00:00.000Z"


def test_parse_due_date_invalid():
    for bad in ["20-10-2026", "tomorrow", "3", "d3", "2026-10", ""]:
        with pytest.raises(ValueError, match="Invalid due date"):
            parse_due_date(bad)


def _tasklists_response():
    """Return a canned tasklists list response for the default-list lookup call."""
    return {"items": [{"id": TASKLIST_ID, "title": "My List"}]}


def test_list_tasks_open_only():
    items = [_task("t1", "Open"), _task("t2", "Done", status="completed")]
    with patch(f"{MODULE}.run_gws_json") as mock_json:
        mock_json.side_effect = [_tasklists_response(), {"items": items}]
        result = list_tasks()
        assert result == items
        args = mock_json.call_args[0]
        assert args[:3] == ("tasks", "tasks", "list")
        assert '"tasklist": "%s"' % TASKLIST_ID in args[4]
        assert '"showCompleted": false' in args[4]


def test_list_tasks_include_completed():
    with patch(f"{MODULE}.run_gws_json") as mock_json:
        mock_json.side_effect = [_tasklists_response(), {}]
        assert list_tasks(include_completed=True) == []
        assert '"showCompleted": true' in mock_json.call_args[0][4]


def test_list_tasks_empty():
    with patch(f"{MODULE}.run_gws_json") as mock_json:
        mock_json.side_effect = [_tasklists_response(), {"items": []}]
        assert list_tasks() == []


def test_get_task():
    with patch(f"{MODULE}.run_gws_json") as mock_json:
        mock_json.side_effect = [_tasklists_response(), _task("t1", "Buy milk")]
        task = get_task("t1")
        assert task["title"] == "Buy milk"
        args = mock_json.call_args[0]
        assert args[:3] == ("tasks", "tasks", "get")
        assert '"task": "t1"' in args[4]


def test_add_task_full():
    with patch(f"{MODULE}.run_gws_json") as mock_json:
        mock_json.side_effect = [
            _tasklists_response(),
            _task("t1", "Buy milk", due="2026-10-20T00:00:00.000Z"),
        ]
        task = add_task("Buy milk", notes="2 liters", due="2026-10-20")
        assert task["id"] == "t1"
        args, kwargs = mock_json.call_args
        assert args[:3] == ("tasks", "tasks", "insert")
        body = kwargs["json_body"]
        assert body["title"] == "Buy milk"
        assert body["notes"] == "2 liters"
        assert body["due"] == "2026-10-20T00:00:00.000Z"


def test_add_task_title_only():
    with patch(f"{MODULE}.run_gws_json") as mock_json:
        mock_json.side_effect = [_tasklists_response(), _task("t1", "Buy milk")]
        add_task("Buy milk")
        body = mock_json.call_args[1]["json_body"]
        assert body == {"title": "Buy milk"}


def test_add_task_invalid_due():
    with patch(f"{MODULE}.run_gws_json") as mock_json:
        mock_json.side_effect = [_tasklists_response()]
        with pytest.raises(ValueError, match="Invalid due date"):
            add_task("Buy milk", due="tomorrow")


@patch(f"{MODULE}._patch_task")
@patch(f"{MODULE}.list_tasks")
def test_mark_task_done_by_title_unique(mock_list, mock_patch):
    mock_list.return_value = [_task("t1", "Buy milk"), _task("t2", "Other")]
    mock_patch.return_value = _task("t1", "Buy milk", status="completed")
    task = mark_task_done_by_title("Buy milk")
    assert task["status"] == "completed"
    mock_patch.assert_called_once_with("t1", {"status": "completed"})


@patch(f"{MODULE}._patch_task")
@patch(f"{MODULE}.list_tasks")
def test_mark_task_done_by_title_no_match(mock_list, mock_patch):
    mock_list.return_value = [_task("t1", "Other")]
    with pytest.raises(ValueError, match="No open task found with title 'Buy milk'"):
        mark_task_done_by_title("Buy milk")
    mock_patch.assert_not_called()


@patch(f"{MODULE}._patch_task")
@patch(f"{MODULE}.list_tasks")
def test_mark_task_done_by_title_multiple_matches(mock_list, mock_patch):
    mock_list.return_value = [_task("t1", "Buy milk"), _task("t2", "Buy milk")]
    with pytest.raises(ValueError, match="2 open tasks with title 'Buy milk'"):
        mark_task_done_by_title("Buy milk")
    mock_patch.assert_not_called()


@patch(f"{MODULE}._patch_task")
@patch(f"{MODULE}.list_tasks")
def test_mark_task_done_by_title_ignores_completed(mock_list, mock_patch):
    mock_list.return_value = [
        _task("t1", "Buy milk", status="completed"),
        _task("t2", "Other"),
    ]
    with pytest.raises(ValueError, match="No open task found"):
        mark_task_done_by_title("Buy milk")
    mock_patch.assert_not_called()


def test_update_task_partial():
    with patch(f"{MODULE}.run_gws_json") as mock_json:
        mock_json.side_effect = [
            _tasklists_response(),
            _task("t1", "Buy milk", due="2026-10-15T00:00:00.000Z"),
        ]
        update_task("t1", due="2026-10-15")
        args, kwargs = mock_json.call_args
        assert args[:3] == ("tasks", "tasks", "patch")
        assert '"task": "t1"' in args[4]
        assert kwargs["json_body"] == {"due": "2026-10-15T00:00:00.000Z"}


def test_update_task_all_fields():
    with patch(f"{MODULE}.run_gws_json") as mock_json:
        mock_json.side_effect = [_tasklists_response(), _task("t1", "New title")]
        update_task("t1", title="New title", notes="New notes", due="1d")
        body = mock_json.call_args[1]["json_body"]
        assert body["title"] == "New title"
        assert body["notes"] == "New notes"
        assert body["due"].endswith("T00:00:00.000Z")
