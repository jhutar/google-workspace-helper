import json
from unittest.mock import patch

from google_workspace_helper.comments import (
    format_comments_markdown,
    list_comments,
)

MODULE = "google_workspace_helper.comments"


def _comment(comment_id, content, **overrides):
    comment = {"id": comment_id, "content": content}
    comment.update(overrides)
    return comment


def test_list_comments_single_page():
    comments = [_comment("c1", "First")]
    with patch(f"{MODULE}.run_gws_json") as mock_json:
        mock_json.return_value = {"comments": comments}
        result = list_comments("doc123")

    assert result == comments
    args = mock_json.call_args[0]
    assert args[:3] == ("drive", "comments", "list")
    params = json.loads(args[4])
    assert params["fileId"] == "doc123"
    assert params["pageSize"] == 100
    assert "comments(" in params["fields"]
    assert "pageToken" not in params


def test_list_comments_follows_pagination():
    first = _comment("c1", "First")
    second = _comment("c2", "Second")
    with patch(f"{MODULE}.run_gws_json") as mock_json:
        mock_json.side_effect = [
            {"comments": [first], "nextPageToken": "page2"},
            {"comments": [second]},
        ]
        result = list_comments("doc123")

    assert result == [first, second]
    assert mock_json.call_count == 2
    second_params = json.loads(mock_json.call_args_list[1][0][4])
    assert second_params["pageToken"] == "page2"


def test_list_comments_empty():
    with patch(f"{MODULE}.run_gws_json") as mock_json:
        mock_json.return_value = {}
        assert list_comments("doc123") == []


def test_format_comments_markdown_thread():
    comments = [
        _comment(
            "c1",
            "Please fix this.",
            author={"displayName": "Alice", "emailAddress": "alice@example.com"},
            createdTime="2026-01-01T10:00:00Z",
            resolved=True,
            quotedFileContent={"value": "Selected text"},
            replies=[
                {
                    "id": "r1",
                    "content": "Done.",
                    "author": {"displayName": "Bob"},
                    "createdTime": "2026-01-02T10:00:00Z",
                }
            ],
        )
    ]

    markdown = format_comments_markdown(comments)

    assert markdown.startswith("# Comments\n")
    assert "## Thread 1: Alice (alice@example.com) [resolved]" in markdown
    assert "Created: 2026-01-01T10:00:00Z" in markdown
    assert "> Selected text" in markdown
    assert "Please fix this." in markdown
    assert "### Replies" in markdown
    assert "**Bob**, 2026-01-02T10:00:00Z" in markdown
    assert "Done." in markdown


def test_format_comments_markdown_multiline_quote():
    comments = [
        _comment(
            "c1",
            "Body",
            quotedFileContent={"value": "line one\nline two"},
        )
    ]

    markdown = format_comments_markdown(comments)

    assert "> line one\n> line two" in markdown


def test_format_comments_markdown_missing_fields():
    markdown = format_comments_markdown([_comment("c1", None)])
    assert "Unknown author" in markdown


def test_format_comments_markdown_empty():
    assert format_comments_markdown([]) == "# Comments\n\n_No comments._\n"
