import pytest
from unittest.mock import patch, MagicMock
import subprocess
import json
import zipfile
import io
from pathlib import Path
from google_workspace_helper.exporter import (
    verify_gws_installed,
    export_file,
    get_file_mime_type,
    verify_pandoc_installed,
    export_spreadsheet_as_csv,
    export_presentation_as_markdown,
)


@patch("shutil.which")
def test_verify_gws_installed_success(mock_which):
    mock_which.return_value = "/usr/bin/gws"
    verify_gws_installed()


@patch("shutil.which")
def test_verify_gws_installed_failure(mock_which):
    mock_which.return_value = None
    with pytest.raises(FileNotFoundError, match="gws CLI tool not found"):
        verify_gws_installed()


@patch("shutil.which")
@patch("subprocess.run")
def test_export_file_success(mock_run, mock_which):
    mock_which.return_value = "/usr/bin/gws"

    def run_side_effect(command, *args, **kwargs):
        # Read the --output flag and write content directly
        output_idx = command.index("--output")
        output_path = command[output_idx + 1]
        Path(output_path).write_text("Markdown file content", encoding="utf-8")
        mock_response = MagicMock()
        mock_response.returncode = 0
        return mock_response

    mock_run.side_effect = run_side_effect

    content = export_file("doc_123")
    assert content == "Markdown file content"
    mock_run.assert_called_once()
    assert any("doc_123" in str(arg) for arg in mock_run.call_args[0][0])


@patch("shutil.which")
@patch("subprocess.run")
def test_export_file_failure(mock_run, mock_which):
    mock_which.return_value = "/usr/bin/gws"

    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="gws ...", stderr=b"Authorization expired"
    )

    with pytest.raises(
        RuntimeError, match="Error executing gws export: Authorization expired"
    ):
        export_file("doc_123")


@patch("google_workspace_helper.exporter.shutil.which")
def test_verify_pandoc_installed_success(mock_which):
    mock_which.return_value = "/usr/bin/pandoc"
    verify_pandoc_installed()


@patch("google_workspace_helper.exporter.shutil.which")
def test_verify_pandoc_installed_failure(mock_which):
    mock_which.return_value = None
    with pytest.raises(FileNotFoundError, match="pandoc is not installed"):
        verify_pandoc_installed()


@patch("google_workspace_helper.exporter.shutil.which")
@patch("google_workspace_helper.exporter.subprocess.run")
def test_get_file_mime_type_spreadsheet(mock_run, mock_which):
    mock_which.return_value = "/usr/bin/gws"
    mock_response = MagicMock()
    mock_response.stdout = json.dumps(
        {"mimeType": "application/vnd.google-apps.spreadsheet"}
    )
    mock_run.return_value = mock_response

    mime = get_file_mime_type("sheet_123")
    assert mime == "application/vnd.google-apps.spreadsheet"


@patch("google_workspace_helper.exporter.shutil.which")
@patch("google_workspace_helper.exporter.subprocess.run")
def test_get_file_mime_type_failure(mock_run, mock_which):
    mock_which.return_value = "/usr/bin/gws"
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="gws", stderr="Not found"
    )
    with pytest.raises(RuntimeError, match="Error fetching file metadata"):
        get_file_mime_type("bad_id")


@patch("google_workspace_helper.exporter.shutil.which")
@patch("google_workspace_helper.exporter.subprocess.run")
def test_export_spreadsheet_as_csv(mock_run, mock_which):
    mock_which.return_value = "/usr/bin/gws"

    def run_side_effect(command, *args, **kwargs):
        output_idx = command.index("--output")
        output_path = command[output_idx + 1]
        Path(output_path).write_text("Name,Age\nAlice,30\n", encoding="utf-8")
        mock_response = MagicMock()
        mock_response.returncode = 0
        return mock_response

    mock_run.side_effect = run_side_effect

    result = export_spreadsheet_as_csv("sheet_123")
    assert result == "Name,Age\nAlice,30\n"


@patch("google_workspace_helper.exporter.shutil.which")
@patch("google_workspace_helper.exporter.subprocess.run")
def test_export_presentation_as_markdown_success(mock_run, mock_which):
    def which_side_effect(name):
        if name in ("gws", "pandoc"):
            return f"/usr/bin/{name}"
        return None

    mock_which.side_effect = which_side_effect

    def run_side_effect(command, *args, **kwargs):
        if "gws" in command[0]:
            output_idx = command.index("--output")
            output_path = command[output_idx + 1]

            # Write a mock zip pptx
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as z:
                slide_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                <p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
                    <p:cSld>
                        <p:spTree>
                            <p:sp>
                                <p:txBody>
                                    <a:p>
                                        <a:r>
                                            <a:t>Slide Title</a:t>
                                        </a:r>
                                    </a:p>
                                    <a:p>
                                        <a:r>
                                            <a:t>Bullet Point 1</a:t>
                                        </a:r>
                                    </a:p>
                                </p:txBody>
                            </p:sp>
                        </p:spTree>
                    </p:cSld>
                </p:sld>
                """
                z.writestr("ppt/slides/slide1.xml", slide_xml)

            Path(output_path).write_bytes(zip_buffer.getvalue())
            mock_res = MagicMock()
            mock_res.returncode = 0
            return mock_res

        elif "pandoc" in command[0]:
            mock_res = MagicMock()
            mock_res.stdout = "# Slide Title\n\n- Bullet Point 1\n"
            mock_res.returncode = 0
            return mock_res

        raise ValueError(f"Unexpected command: {command}")

    mock_run.side_effect = run_side_effect

    result = export_presentation_as_markdown("slides_123")
    assert "# Slide Title" in result
    assert "- Bullet Point 1" in result
    assert mock_run.call_count == 2


@patch("google_workspace_helper.exporter.shutil.which")
def test_export_presentation_no_pandoc(mock_which):
    def which_side_effect(name):
        if name == "gws":
            return "/usr/bin/gws"
        return None

    mock_which.side_effect = which_side_effect
    with pytest.raises(FileNotFoundError, match="pandoc is not installed"):
        export_presentation_as_markdown("slides_123")
