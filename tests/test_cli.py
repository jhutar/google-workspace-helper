import pytest
import argparse
from google_workspace_helper.cli import extract_file_id, validate_file_id, handle_export


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
