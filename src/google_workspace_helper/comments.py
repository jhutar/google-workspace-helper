import json
import logging

from google_workspace_helper.gws_runner import run_gws_json

logger = logging.getLogger("google_workspace_helper")

_COMMENT_FIELDS = (
    "comments("
    "id,content,author(displayName,emailAddress),createdTime,modifiedTime,resolved,"
    "quotedFileContent,replies(id,content,author(displayName,emailAddress),"
    "createdTime,modifiedTime)"
    "),nextPageToken"
)


def _fetch_comments_page(file_id: str, page_token: str | None = None) -> dict:
    """Fetch one page of comment threads for a Drive file."""
    params: dict[str, str | int] = {
        "fileId": file_id,
        "fields": _COMMENT_FIELDS,
        "pageSize": 100,
    }
    if page_token is not None:
        params["pageToken"] = page_token
    logger.debug("Fetching comments for file_id=%s", file_id)
    return run_gws_json("drive", "comments", "list", "--params", json.dumps(params))


def list_comments(file_id: str) -> list[dict]:
    """Fetch all comment threads for a Drive file, following pagination tokens."""
    comments: list[dict] = []
    page_token: str | None = None
    while True:
        data = _fetch_comments_page(file_id, page_token)
        comments.extend(data.get("comments", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    logger.debug("Fetched %d comment threads for file_id=%s", len(comments), file_id)
    return comments


def _format_author(author: dict | None) -> str:
    """Format a comment author as 'Name (email)'."""
    if not author:
        return "Unknown author"
    name = author.get("displayName") or "Unknown author"
    email = author.get("emailAddress")
    return f"{name} ({email})" if email else name


def format_comments_markdown(comments: list[dict]) -> str:
    """Render comment threads as readable Markdown."""
    lines = ["# Comments", ""]
    if not comments:
        lines.append("_No comments._")
        return "\n".join(lines) + "\n"

    for index, comment in enumerate(comments, start=1):
        resolved = " [resolved]" if comment.get("resolved") else ""
        author = _format_author(comment.get("author"))
        lines.append(f"## Thread {index}: {author}{resolved}")
        created = comment.get("createdTime")
        if created:
            lines.append(f"Created: {created}")

        quoted = comment.get("quotedFileContent") or {}
        quoted_text = quoted.get("value")
        if quoted_text:
            lines.append("")
            lines.extend(f"> {line}" for line in quoted_text.splitlines())

        body = comment.get("content")
        if body:
            lines.append("")
            lines.append(body)

        replies = comment.get("replies") or []
        if replies:
            lines.append("")
            lines.append("### Replies")
            for reply in replies:
                lines.append("")
                reply_author = _format_author(reply.get("author"))
                reply_created = reply.get("createdTime")
                lines.append(
                    f"**{reply_author}**, {reply_created}"
                    if reply_created
                    else f"**{reply_author}**"
                )
                reply_body = reply.get("content")
                if reply_body:
                    lines.append("")
                    lines.append(reply_body)

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
