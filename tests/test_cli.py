import pytest
import argparse
from google_workspace_helper.cli import validate_file_id, handle_export

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
