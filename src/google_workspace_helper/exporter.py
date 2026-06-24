import shutil
import subprocess
import json
import sys

def verify_gws_installed() -> None:
    """Verifies that the gws CLI tool is installed and accessible in system PATH."""
    if not shutil.which("gws"):
        raise FileNotFoundError("Error: gws CLI tool not found in system PATH. Please install it first.")

def export_file(file_id: str, mime_type: str = "text/markdown") -> str:
    """Executes gws command to export the Google Drive file to markdown."""
    verify_gws_installed()

    # Construct the JSON params string
    params_dict = {
        "fileId": file_id,
        "mimeType": mime_type
    }
    params_json = json.dumps(params_dict)

    command = [
        "gws",
        "drive",
        "files",
        "export",
        "--params",
        params_json
    ]

    try:
        # Run subprocess and capture both stdout and stderr
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        # If gws prints to stdout, return it
        if result.stdout.strip():
            return result.stdout
        else:
            # If stdout is empty, check if gws downloaded a file in the current directory
            # or raise an error. We default to assuming gws returns the content on stdout
            # when piped or run.
            raise ValueError("Error: gws export command succeeded but returned empty stdout.")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        raise RuntimeError(f"Error executing gws export: {error_msg}") from e
