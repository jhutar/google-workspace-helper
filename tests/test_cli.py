import pytest
import argparse
from unittest.mock import patch
from google_workspace_helper.cli import (
    extract_file_id,
    validate_file_id,
    handle_export,
    handle_append,
)


def test_extract_file_id_direct():
    # If not a URL, should return the input unchanged
    assert (
        extract_file_id("1qXUszdKD2ytd7vkl1wup6d32ATb_Rl4IH0_xeOxceXo")
        == "1qXUszdKD2ytd7vkl1wup6d32ATb_Rl4IH0_xeOxceXo"
    )
    assert extract_file_id("simple-id") == "simple-id"
    assert extract_file_id("") == ""


def test_extract_file_id_urls():
    # Documents URL
    doc_url = "https://docs.google.com/document/d/1qXUszdKD2ytd7vkl1wup6d32ATb_Rl4IH0_xeOxceXo/edit"
    assert extract_file_id(doc_url) == "1qXUszdKD2ytd7vkl1wup6d32ATb_Rl4IH0_xeOxceXo"

    # Spreadsheets URL (with query params)
    sheet_url = "https://docs.google.com/spreadsheets/d/1bK2zYUxtmnj2tco3sJQcFwLv2roEiS7jZg5_q9I1ciA/edit?usp=drive_link"
    assert extract_file_id(sheet_url) == "1bK2zYUxtmnj2tco3sJQcFwLv2roEiS7jZg5_q9I1ciA"

    # Presentation/Slides URL
    slides_url = "https://docs.google.com/presentation/d/1presentation-id-123_abc/edit#slide=id.g10b"
    assert extract_file_id(slides_url) == "1presentation-id-123_abc"

    # Drive file link via URL id param
    drive_url = (
        "https://drive.google.com/open?id=1qXUszdKD2ytd7vkl1wup6d32ATb_Rl4IH0_xeOxceXo"
    )
    assert extract_file_id(drive_url) == "1qXUszdKD2ytd7vkl1wup6d32ATb_Rl4IH0_xeOxceXo"


def test_extract_file_id_invalid_url():
    with pytest.raises(ValueError, match="Could not extract Google Drive File ID"):
        extract_file_id("https://google.com/some/random/path")


def test_validate_file_id_valid():
    # Safe Alphanumeric / standard IDs
    validate_file_id("1qXUszdKD2ytd7vkl1wup6d32ATb_Rl4IH0_xeOxceXo")
    validate_file_id("simple_id-123")


def test_validate_file_id_invalid():
    # Shell expansion or invalid chars
    with pytest.raises(ValueError, match="Invalid File ID"):
        validate_file_id("bad; id")
    with pytest.raises(ValueError, match="Invalid File ID"):
        validate_file_id("id$with_dollar")
    with pytest.raises(ValueError, match="Invalid File ID"):
        validate_file_id("id/with/slash")
    with pytest.raises(ValueError, match="File ID cannot be empty"):
        validate_file_id("")


def test_handle_export_invalid_id(capsys):
    # Setup standard CLI arguments namespace
    args = argparse.Namespace(file_id="bad; id", output="test.md")
    status = handle_export(args)
    assert status == 1
    captured = capsys.readouterr()
    assert "Invalid File ID" in captured.err


@patch("google_workspace_helper.cli.get_file_mime_type")
@patch("google_workspace_helper.cli.export_file")
@patch("google_workspace_helper.cli.post_process_markdown")
def test_handle_export_to_stdout(mock_process, mock_export, mock_mime, capsys):
    mock_mime.return_value = "application/vnd.google-apps.document"
    mock_export.return_value = "raw markdown content"
    mock_process.return_value = "# Processed Markdown"

    args = argparse.Namespace(file_id="doc_123", output=None)
    status = handle_export(args)
    assert status == 0

    captured = capsys.readouterr()
    assert captured.out == "# Processed Markdown"
    assert "Success: Exported" not in captured.out


@patch("google_workspace_helper.cli.get_file_mime_type")
@patch("google_workspace_helper.cli.export_file")
@patch("google_workspace_helper.cli.post_process_markdown")
def test_handle_export_to_file(mock_process, mock_export, mock_mime, tmp_path, capsys):
    mock_mime.return_value = "application/vnd.google-apps.document"
    mock_export.return_value = "raw markdown content"
    mock_process.return_value = "# Processed Markdown"

    out_file = tmp_path / "test_out.md"
    args = argparse.Namespace(file_id="doc_123", output=str(out_file))
    status = handle_export(args)
    assert status == 0

    assert out_file.exists()
    assert out_file.read_text(encoding="utf-8") == "# Processed Markdown"

    captured = capsys.readouterr()
    assert f"Success: Exported clean markdown to {out_file}" in captured.out


def test_handle_append_invalid_id(capsys):
    args = argparse.Namespace(file_id="bad; id", text="hello", image=None)
    status = handle_append(args)
    assert status == 1
    captured = capsys.readouterr()
    assert "Invalid File ID" in captured.err


def test_handle_append_no_flags(capsys):
    args = argparse.Namespace(file_id="doc123", text=None, image=None)
    status = handle_append(args)
    assert status == 1
    captured = capsys.readouterr()
    assert "At least one of --text or --image" in captured.err


def test_handle_append_image_not_found(capsys):
    args = argparse.Namespace(
        file_id="doc123", text=None, image="/nonexistent/image.png"
    )
    status = handle_append(args)
    assert status == 1
    captured = capsys.readouterr()
    assert "Image file not found" in captured.err


@patch("google_workspace_helper.cli.append_to_document")
def test_handle_append_text_only(mock_append, capsys):
    args = argparse.Namespace(file_id="doc123", text="Hello world", image=None)
    status = handle_append(args)
    assert status == 0
    mock_append.assert_called_once_with("doc123", text="Hello world", image_path=None)
    captured = capsys.readouterr()
    assert "Success" in captured.out


@patch("google_workspace_helper.cli.append_to_document")
def test_handle_append_with_image(mock_append, capsys, tmp_path):
    image_file = tmp_path / "graph.png"
    image_file.write_bytes(b"\x89PNG")
    args = argparse.Namespace(file_id="doc123", text="desc", image=str(image_file))
    status = handle_append(args)
    assert status == 0
    mock_append.assert_called_once_with("doc123", text="desc", image_path=image_file)


@patch("google_workspace_helper.cli.append_to_document")
def test_handle_append_url_extraction(mock_append, capsys):
    url = "https://docs.google.com/document/d/abc123_def/edit"
    args = argparse.Namespace(file_id=url, text="test", image=None)
    status = handle_append(args)
    assert status == 0
    mock_append.assert_called_once_with("abc123_def", text="test", image_path=None)


@patch("google_workspace_helper.cli.append_to_document")
def test_handle_append_error(mock_append, capsys):
    mock_append.side_effect = RuntimeError("API error")
    args = argparse.Namespace(file_id="doc123", text="hello", image=None)
    status = handle_append(args)
    assert status == 1
    captured = capsys.readouterr()
    assert "API error" in captured.err
