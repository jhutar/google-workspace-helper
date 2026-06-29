import json
import subprocess

import pytest
from unittest.mock import patch, MagicMock

from google_workspace_helper.gws_runner import (
    check_gws_installed,
    run_gws,
    run_gws_json,
    run_gws_to_file,
    run_gws_upload,
)


@patch("google_workspace_helper.gws_runner.shutil.which")
def test_check_gws_installed_success(mock_which):
    mock_which.return_value = "/usr/bin/gws"
    check_gws_installed()


@patch("google_workspace_helper.gws_runner.shutil.which")
def test_check_gws_installed_failure(mock_which):
    mock_which.return_value = None
    with pytest.raises(FileNotFoundError, match="gws CLI tool not found"):
        check_gws_installed()


@patch("google_workspace_helper.gws_runner.subprocess.run")
def test_run_gws_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    run_gws("drive", "files", "delete", "--params", '{"fileId": "abc"}')
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "gws"
    assert "delete" in cmd


@patch("google_workspace_helper.gws_runner.subprocess.run")
def test_run_gws_failure(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="gws", stderr="permission denied"
    )
    with pytest.raises(RuntimeError, match="gws command failed: permission denied"):
        run_gws("drive", "files", "delete", "--params", '{"fileId": "abc"}')


@patch("google_workspace_helper.gws_runner.subprocess.run")
def test_run_gws_json_success(mock_run):
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps({"mimeType": "application/vnd.google-apps.document"}),
    )
    result = run_gws_json("drive", "files", "get", "--params", '{"fileId": "abc"}')
    assert result["mimeType"] == "application/vnd.google-apps.document"


@patch("google_workspace_helper.gws_runner.subprocess.run")
def test_run_gws_json_with_body(mock_run):
    mock_run.return_value = MagicMock(
        returncode=0, stdout=json.dumps({"documentId": "doc123"})
    )
    body = {"requests": [{"insertText": {"text": "hello"}}]}
    result = run_gws_json(
        "docs",
        "documents",
        "batchUpdate",
        "--params",
        '{"documentId": "doc123"}',
        json_body=body,
    )
    assert result["documentId"] == "doc123"
    cmd = mock_run.call_args[0][0]
    assert "--json" in cmd
    json_idx = cmd.index("--json")
    assert json.loads(cmd[json_idx + 1]) == body


@patch("google_workspace_helper.gws_runner.subprocess.run")
def test_run_gws_json_invalid_response(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="not json")
    with pytest.raises(RuntimeError, match="Failed to parse gws JSON response"):
        run_gws_json("drive", "files", "get", "--params", '{"fileId": "abc"}')


@patch("google_workspace_helper.gws_runner.subprocess.run")
def test_run_gws_json_failure(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="gws", stderr="not found"
    )
    with pytest.raises(RuntimeError, match="gws command failed: not found"):
        run_gws_json("drive", "files", "get", "--params", '{"fileId": "abc"}')


@patch("google_workspace_helper.gws_runner.subprocess.run")
def test_run_gws_to_file_success(mock_run, tmp_path):
    output_file = tmp_path / "export.md"

    def side_effect(cmd, **kwargs):
        output_file.write_text("exported content", encoding="utf-8")
        return MagicMock(returncode=0)

    mock_run.side_effect = side_effect
    result = run_gws_to_file(
        "drive",
        "files",
        "export",
        "--params",
        '{"fileId": "abc"}',
        output_path=output_file,
    )
    assert result == output_file
    assert output_file.read_text() == "exported content"


@patch("google_workspace_helper.gws_runner.subprocess.run")
def test_run_gws_to_file_not_created(mock_run, tmp_path):
    output_file = tmp_path / "missing.md"
    mock_run.return_value = MagicMock(returncode=0)
    with pytest.raises(FileNotFoundError, match="Output file was not created"):
        run_gws_to_file(
            "drive",
            "files",
            "export",
            "--params",
            '{"fileId": "abc"}',
            output_path=output_file,
        )


@patch("google_workspace_helper.gws_runner.subprocess.run")
def test_run_gws_to_file_failure(mock_run, tmp_path):
    output_file = tmp_path / "export.md"
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="gws", stderr="auth expired"
    )
    with pytest.raises(RuntimeError, match="gws command failed: auth expired"):
        run_gws_to_file(
            "drive",
            "files",
            "export",
            "--params",
            '{"fileId": "abc"}',
            output_path=output_file,
        )


@patch("google_workspace_helper.gws_runner.subprocess.run")
def test_run_gws_upload_success(mock_run, tmp_path):
    upload_file = tmp_path / "image.png"
    upload_file.write_bytes(b"\x89PNG")
    mock_run.return_value = MagicMock(
        returncode=0, stdout=json.dumps({"id": "uploaded_123"})
    )
    result = run_gws_upload(
        "drive",
        "files",
        "create",
        upload_path=upload_file,
        upload_content_type="image/png",
    )
    assert result["id"] == "uploaded_123"
    cmd = mock_run.call_args[0][0]
    assert "--upload" in cmd
    assert "--upload-content-type" in cmd
    ct_idx = cmd.index("--upload-content-type")
    assert cmd[ct_idx + 1] == "image/png"


@patch("google_workspace_helper.gws_runner.subprocess.run")
def test_run_gws_upload_without_content_type(mock_run, tmp_path):
    upload_file = tmp_path / "image.png"
    upload_file.write_bytes(b"\x89PNG")
    mock_run.return_value = MagicMock(
        returncode=0, stdout=json.dumps({"id": "uploaded_456"})
    )
    result = run_gws_upload("drive", "files", "create", upload_path=upload_file)
    assert result["id"] == "uploaded_456"
    cmd = mock_run.call_args[0][0]
    assert "--upload-content-type" not in cmd


@patch("google_workspace_helper.gws_runner.subprocess.run")
def test_run_gws_upload_failure(mock_run, tmp_path):
    upload_file = tmp_path / "image.png"
    upload_file.write_bytes(b"\x89PNG")
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="gws", stderr="quota exceeded"
    )
    with pytest.raises(RuntimeError, match="gws command failed: quota exceeded"):
        run_gws_upload(
            "drive",
            "files",
            "create",
            upload_path=upload_file,
            upload_content_type="image/png",
        )


@patch("google_workspace_helper.gws_runner.subprocess.run")
def test_run_gws_upload_invalid_response(mock_run, tmp_path):
    upload_file = tmp_path / "image.png"
    upload_file.write_bytes(b"\x89PNG")
    mock_run.return_value = MagicMock(returncode=0, stdout="not json")
    with pytest.raises(RuntimeError, match="Failed to parse gws upload response"):
        run_gws_upload(
            "drive",
            "files",
            "create",
            upload_path=upload_file,
            upload_content_type="image/png",
        )
