import pytest
from unittest.mock import patch, MagicMock
import subprocess
from google_workspace_helper.exporter import verify_gws_installed, export_file

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
        returncode=1,
        cmd="gws ...",
        stderr="Authorization expired"
    )
    
    with pytest.raises(RuntimeError, match="Error executing gws export: Authorization expired"):
        export_file("doc_123")
