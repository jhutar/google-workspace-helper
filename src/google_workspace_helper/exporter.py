import logging
import shutil
import subprocess
import json
import tempfile
from pathlib import Path

logger = logging.getLogger("google_workspace_helper")

MIME_SPREADSHEET = "application/vnd.google-apps.spreadsheet"
MIME_PRESENTATION = "application/vnd.google-apps.presentation"
MIME_DOCUMENT = "application/vnd.google-apps.document"


def verify_gws_installed() -> None:
    if not shutil.which("gws"):
        raise FileNotFoundError(
            "Error: gws CLI tool not found in system PATH. Please install it first."
        )


def verify_pandoc_installed() -> None:
    if not shutil.which("pandoc"):
        raise FileNotFoundError(
            "Error: pandoc is not installed. Please install pandoc to convert "
            "presentations to Markdown. Visit https://pandoc.org/installing.html"
        )


def get_file_mime_type(file_id: str) -> str:
    verify_gws_installed()
    params_json = json.dumps({"fileId": file_id, "fields": "mimeType"})
    command = ["gws", "drive", "files", "get", "--params", params_json]
    logger.debug("Fetching mime type for file_id=%s", file_id)
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        mime_type = data.get("mimeType", "")
        logger.debug("Detected mime type: %s", mime_type)
        return mime_type
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        raise RuntimeError(f"Error fetching file metadata: {error_msg}") from e
    except (json.JSONDecodeError, KeyError) as e:
        raise RuntimeError(f"Error parsing file metadata response: {e}") from e


def export_file(file_id: str, mime_type: str = "text/markdown") -> str:
    verify_gws_installed()
    params_dict = {"fileId": file_id, "mimeType": mime_type}
    params_json = json.dumps(params_dict)
    command = ["gws", "drive", "files", "export", "--params", params_json]
    logger.debug("Exporting file_id=%s with mime_type=%s", file_id, mime_type)
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        if result.stdout.strip():
            return result.stdout
        else:
            raise ValueError(
                "Error: gws export command succeeded but returned empty stdout."
            )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        raise RuntimeError(f"Error executing gws export: {error_msg}") from e


def export_spreadsheet_as_csv(file_id: str) -> str:
    verify_gws_installed()
    logger.debug("Exporting spreadsheet file_id=%s as CSV", file_id)
    logger.warning(
        "Only the first sheet of the spreadsheet will be exported. "
        "Multi-sheet export is not supported."
    )
    return export_file(file_id, mime_type="text/csv")


def export_presentation_as_markdown(file_id: str) -> str:
    verify_gws_installed()
    verify_pandoc_installed()
    logger.debug("Exporting presentation file_id=%s via PPTX+pandoc", file_id)

    pptx_mime = (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    params_json = json.dumps({"fileId": file_id, "mimeType": pptx_mime})
    command = ["gws", "drive", "files", "export", "--params", params_json]

    with tempfile.TemporaryDirectory() as tmp_dir:
        pptx_path = Path(tmp_dir) / f"{file_id}.pptx"

        try:
            result = subprocess.run(command, capture_output=True, check=True)
            if not result.stdout:
                raise ValueError(
                    "Error: gws export command succeeded but returned empty output."
                )
            pptx_path.write_bytes(result.stdout)
            logger.debug("Downloaded PPTX to %s", pptx_path)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode().strip() if e.stderr else str(e)
            raise RuntimeError(f"Error downloading presentation: {error_msg}") from e

        pandoc_cmd = [
            "pandoc",
            str(pptx_path),
            "-f",
            "pptx",
            "-t",
            "markdown",
            "-o",
            "-",
        ]
        try:
            pandoc_result = subprocess.run(
                pandoc_cmd, capture_output=True, text=True, check=True
            )
            logger.debug("Pandoc conversion complete for file_id=%s", file_id)
            return pandoc_result.stdout
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            raise RuntimeError(
                f"Error converting presentation with pandoc: {error_msg}"
            ) from e
