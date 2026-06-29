import json
import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger("google_workspace_helper")


def check_gws_installed() -> None:
    if not shutil.which("gws"):
        raise FileNotFoundError(
            "Error: gws CLI tool not found in system PATH. Please install it first."
        )


def _run_gws_subprocess(cmd: list[str]) -> subprocess.CompletedProcess:
    logger.debug("Running gws command: %s", " ".join(cmd))
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        raise RuntimeError(f"gws command failed: {error_msg}") from e


def run_gws(*args: str) -> None:
    _run_gws_subprocess(["gws", *args])


def run_gws_json(*args: str, json_body: dict | None = None) -> dict:
    cmd = ["gws", *args]
    if json_body is not None:
        cmd.extend(["--json", json.dumps(json_body)])
    result = _run_gws_subprocess(cmd)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse gws JSON response: {e}") from e


def run_gws_to_file(*args: str, output_path: Path) -> Path:
    cmd = ["gws", *args, "--output", str(output_path)]
    _run_gws_subprocess(cmd)
    if not output_path.exists():
        raise FileNotFoundError(
            f"Error: Output file was not created by gws: {output_path}"
        )
    return output_path


def run_gws_upload(
    *args: str,
    upload_path: Path,
    upload_content_type: str | None = None,
) -> dict:
    cmd = ["gws", *args, "--upload", str(upload_path)]
    if upload_content_type is not None:
        cmd.extend(["--upload-content-type", upload_content_type])
    result = _run_gws_subprocess(cmd)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse gws upload response: {e}") from e
