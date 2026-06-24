import csv
import io
import logging
import re
import base64
from pathlib import Path

logger = logging.getLogger("google_workspace_helper")

IMAGE_RE = re.compile(
    r"data:image/(?P<ext>[a-zA-Z0-9+-.]+);base64,(?P<data>[a-zA-Z0-9+/= \r\n]+)"
)


def post_process_markdown(markdown_content: str, file_id: str) -> str:
    """Extracts inline base64 images, decodes them to /tmp/<file_id>/, and replaces the links."""
    temp_dir = Path(f"/tmp/{file_id}")
    image_index = 1

    def replace_match(match: re.Match) -> str:
        nonlocal image_index

        # Ensure temporary directory exists only when at least one image is processed
        temp_dir.mkdir(parents=True, exist_ok=True)

        ext = match.group("ext")
        # Normalize extension: jpeg -> jpg
        if ext.lower() == "jpeg":
            ext = "jpg"

        raw_data = (
            match.group("data")
            .strip()
            .replace("\r", "")
            .replace("\n", "")
            .replace(" ", "")
        )

        try:
            decoded_bytes = base64.b64decode(raw_data)
        except Exception as e:
            raise ValueError(
                f"Error: Failed to decode base64 image at index {image_index}: {e}"
            ) from e

        file_name = f"image_{image_index}.{ext}"
        file_path = temp_dir / file_name

        # Write decoded binary data to local file
        file_path.write_bytes(decoded_bytes)

        # Return the clean local relative path
        local_ref = f"/tmp/{file_id}/{file_name}"
        image_index += 1
        return local_ref

    processed_content = IMAGE_RE.sub(replace_match, markdown_content)
    return processed_content


def _escape_pipe(cell: str) -> str:
    return cell.replace("|", "\\|")


def csv_to_markdown_table(csv_content: str) -> str:
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)

    if not rows:
        return ""

    header = rows[0]
    escaped_header = [_escape_pipe(c.strip()) for c in header]
    lines = ["| " + " | ".join(escaped_header) + " |"]
    lines.append("| " + " | ".join("---" for _ in header) + " |")

    for row in rows[1:]:
        while len(row) < len(header):
            row.append("")
        escaped = [_escape_pipe(c.strip()) for c in row[: len(header)]]
        lines.append("| " + " | ".join(escaped) + " |")

    return "\n".join(lines) + "\n"
