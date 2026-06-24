import pytest
from unittest.mock import patch, MagicMock
import subprocess
import json
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
    # Should not raise exception
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

    # Mock subprocess success returning content
    mock_response = MagicMock()
    mock_response.stdout = "Markdown file content"
    mock_response.return_code = 0
    mock_run.return_value = mock_response

    content = export_file("doc_123")
    assert content == "Markdown file content"
    mock_run.assert_called_once()
    assert "doc_123" in mock_run.call_args[0][0][-1]


@patch("shutil.which")
@patch("subprocess.run")
def test_export_file_failure(mock_run, mock_which):
    mock_which.return_value = "/usr/bin/gws"

    # Mock subprocess failure
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="gws ...", stderr="Authorization expired"
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
    mock_response = MagicMock()
    mock_response.stdout = "Name,Age\nAlice,30\n"
    mock_run.return_value = mock_response

    result = export_spreadsheet_as_csv("sheet_123")
    assert result == "Name,Age\nAlice,30\n"
    call_args = mock_run.call_args[0][0]
    assert "text/csv" in call_args[-1]


@patch("google_workspace_helper.exporter.shutil.which")
@patch("google_workspace_helper.exporter.subprocess.run")
def test_export_presentation_as_markdown_success(mock_run, mock_which):
    mock_which.return_value = "/usr/bin/pandoc"

    gws_response = MagicMock()
    gws_response.stdout = b"fake pptx bytes"

    pandoc_response = MagicMock()
    pandoc_response.stdout = "# Slide 1\n\nContent here\n"

    mock_run.side_effect = [gws_response, pandoc_response]

    result = export_presentation_as_markdown("slides_123")
    assert "# Slide 1" in result
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
