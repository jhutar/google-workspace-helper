import pytest
from unittest.mock import patch, MagicMock
import zipfile
import io
from google_workspace_helper.exporter import (
    export_file,
    get_file_mime_type,
    verify_pandoc_installed,
    export_spreadsheet_as_csv,
    export_presentation_as_markdown,
)


@patch("google_workspace_helper.exporter.shutil.which")
def test_verify_pandoc_installed_success(mock_which):
    mock_which.return_value = "/usr/bin/pandoc"
    verify_pandoc_installed()


@patch("google_workspace_helper.exporter.shutil.which")
def test_verify_pandoc_installed_failure(mock_which):
    mock_which.return_value = None
    with pytest.raises(FileNotFoundError, match="pandoc is not installed"):
        verify_pandoc_installed()


@patch("google_workspace_helper.exporter.run_gws_json")
def test_get_file_mime_type_spreadsheet(mock_run_json):
    mock_run_json.return_value = {"mimeType": "application/vnd.google-apps.spreadsheet"}
    mime = get_file_mime_type("sheet_123")
    assert mime == "application/vnd.google-apps.spreadsheet"
    mock_run_json.assert_called_once()


@patch("google_workspace_helper.exporter.run_gws_json")
def test_get_file_mime_type_failure(mock_run_json):
    mock_run_json.side_effect = RuntimeError("gws command failed: Not found")
    with pytest.raises(RuntimeError, match="gws command failed"):
        get_file_mime_type("bad_id")


@patch("google_workspace_helper.exporter.run_gws_to_file")
def test_export_file_success(mock_to_file):
    def side_effect(*args, output_path):
        output_path.write_text("Markdown file content", encoding="utf-8")
        return output_path

    mock_to_file.side_effect = side_effect
    content = export_file("doc_123")
    assert content == "Markdown file content"
    mock_to_file.assert_called_once()


@patch("google_workspace_helper.exporter.run_gws_to_file")
def test_export_file_failure(mock_to_file):
    mock_to_file.side_effect = RuntimeError("gws command failed: Authorization expired")
    with pytest.raises(RuntimeError, match="Authorization expired"):
        export_file("doc_123")


@patch("google_workspace_helper.exporter.run_gws_to_file")
def test_export_spreadsheet_as_csv(mock_to_file):
    def side_effect(*args, output_path):
        output_path.write_text("Name,Age\nAlice,30\n", encoding="utf-8")
        return output_path

    mock_to_file.side_effect = side_effect
    result = export_spreadsheet_as_csv("sheet_123")
    assert result == "Name,Age\nAlice,30\n"


@patch("google_workspace_helper.exporter.subprocess.run")
@patch("google_workspace_helper.exporter.run_gws_to_file")
@patch("google_workspace_helper.exporter.shutil.which")
def test_export_presentation_as_markdown_success(
    mock_which, mock_to_file, mock_subprocess_run
):
    mock_which.return_value = "/usr/bin/pandoc"

    def gws_side_effect(*args, output_path):
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
        output_path.write_bytes(zip_buffer.getvalue())
        return output_path

    mock_to_file.side_effect = gws_side_effect

    pandoc_result = MagicMock()
    pandoc_result.stdout = "# Slide Title\n\n- Bullet Point 1\n"
    pandoc_result.returncode = 0
    mock_subprocess_run.return_value = pandoc_result

    result = export_presentation_as_markdown("slides_123")
    assert "# Slide Title" in result
    assert "- Bullet Point 1" in result
    mock_to_file.assert_called_once()
    mock_subprocess_run.assert_called_once()


@patch("google_workspace_helper.exporter.shutil.which")
def test_export_presentation_no_pandoc(mock_which):
    mock_which.return_value = None
    with pytest.raises(FileNotFoundError, match="pandoc is not installed"):
        export_presentation_as_markdown("slides_123")
