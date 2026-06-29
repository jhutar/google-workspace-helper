import pytest
from unittest.mock import patch, call
from pathlib import Path

from google_workspace_helper.appender import (
    append_text,
    append_image,
    append_to_document,
)

MODULE = "google_workspace_helper.appender"


@patch(f"{MODULE}.run_gws_json")
def test_append_text(mock_json):
    mock_json.return_value = {"documentId": "doc123"}
    append_text("doc123", "Hello world")
    mock_json.assert_called_once()
    args, kwargs = mock_json.call_args
    assert "batchUpdate" in args
    body = kwargs["json_body"]
    assert body["requests"][0]["insertText"]["text"] == "\nHello world"


@patch(f"{MODULE}.run_gws_json")
def test_append_text_with_newlines(mock_json):
    mock_json.return_value = {"documentId": "doc123"}
    append_text("doc123", "Line 1\nLine 2\nLine 3")
    args, kwargs = mock_json.call_args
    body = kwargs["json_body"]
    assert "Line 1\nLine 2\nLine 3" in body["requests"][0]["insertText"]["text"]


@patch(f"{MODULE}.run_gws")
@patch(f"{MODULE}.run_gws_json")
@patch(f"{MODULE}.run_gws_upload")
@patch(f"{MODULE}._get_user_domain")
def test_append_image_success(mock_domain, mock_upload, mock_json, mock_gws, tmp_path):
    image_file = tmp_path / "graph.png"
    image_file.write_bytes(b"\x89PNG")

    mock_domain.return_value = "example.com"
    mock_upload.return_value = {"id": "uploaded_123"}
    mock_json.side_effect = [
        {"kind": "drive#permission"},
        {"webContentLink": "https://drive.google.com/uc?id=uploaded_123&export=download"},
        {"documentId": "doc123"},
    ]

    append_image("doc123", image_file)

    mock_upload.assert_called_once()
    assert mock_json.call_count == 3
    mock_gws.assert_called_once()
    delete_args = mock_gws.call_args[0]
    assert "delete" in delete_args


@patch(f"{MODULE}.run_gws")
@patch(f"{MODULE}.run_gws_json")
@patch(f"{MODULE}.run_gws_upload")
@patch(f"{MODULE}._get_user_domain")
def test_append_image_insert_fails_cleanup_succeeds(
    mock_domain, mock_upload, mock_json, mock_gws, tmp_path
):
    image_file = tmp_path / "graph.png"
    image_file.write_bytes(b"\x89PNG")

    mock_domain.return_value = "example.com"
    mock_upload.return_value = {"id": "uploaded_123"}
    mock_json.side_effect = [
        {"kind": "drive#permission"},
        {"webContentLink": "https://drive.google.com/uc?id=uploaded_123&export=download"},
        RuntimeError("Insert failed: quota exceeded"),
    ]

    with pytest.raises(RuntimeError, match="Insert failed"):
        append_image("doc123", image_file)

    mock_gws.assert_called_once()
    delete_args = mock_gws.call_args[0]
    assert "delete" in delete_args


@patch(f"{MODULE}.run_gws")
@patch(f"{MODULE}.run_gws_json")
@patch(f"{MODULE}.run_gws_upload")
@patch(f"{MODULE}._get_user_domain")
def test_append_image_insert_succeeds_cleanup_fails(
    mock_domain, mock_upload, mock_json, mock_gws, tmp_path
):
    image_file = tmp_path / "graph.png"
    image_file.write_bytes(b"\x89PNG")

    mock_domain.return_value = "example.com"
    mock_upload.return_value = {"id": "uploaded_123"}
    mock_json.side_effect = [
        {"kind": "drive#permission"},
        {"webContentLink": "https://drive.google.com/uc?id=uploaded_123&export=download"},
        {"documentId": "doc123"},
    ]
    mock_gws.side_effect = RuntimeError("Delete failed: network error")

    with pytest.raises(RuntimeError, match="Delete failed"):
        append_image("doc123", image_file)


@patch(f"{MODULE}.run_gws")
@patch(f"{MODULE}.run_gws_json")
@patch(f"{MODULE}.run_gws_upload")
@patch(f"{MODULE}._get_user_domain")
def test_append_image_both_fail(
    mock_domain, mock_upload, mock_json, mock_gws, tmp_path
):
    image_file = tmp_path / "graph.png"
    image_file.write_bytes(b"\x89PNG")

    mock_domain.return_value = "example.com"
    mock_upload.return_value = {"id": "uploaded_123"}
    mock_json.side_effect = [
        {"kind": "drive#permission"},
        {"webContentLink": "https://drive.google.com/uc?id=uploaded_123&export=download"},
        RuntimeError("Insert failed"),
    ]
    mock_gws.side_effect = RuntimeError("Delete failed")

    with pytest.raises(RuntimeError):
        append_image("doc123", image_file)

    mock_gws.assert_called_once()


@patch(f"{MODULE}.run_gws")
@patch(f"{MODULE}.run_gws_json")
@patch(f"{MODULE}.run_gws_upload")
@patch(f"{MODULE}._get_user_domain")
def test_append_image_no_web_content_link(
    mock_domain, mock_upload, mock_json, mock_gws, tmp_path
):
    image_file = tmp_path / "graph.png"
    image_file.write_bytes(b"\x89PNG")

    mock_domain.return_value = "example.com"
    mock_upload.return_value = {"id": "uploaded_123"}
    mock_json.side_effect = [
        {"kind": "drive#permission"},
        {},
    ]

    with pytest.raises(RuntimeError, match="webContentLink"):
        append_image("doc123", image_file)

    mock_gws.assert_called_once()


@patch(f"{MODULE}.append_image")
@patch(f"{MODULE}.append_text")
@patch(f"{MODULE}._verify_is_document")
def test_append_to_document_text_and_image(mock_verify, mock_text, mock_image, tmp_path):
    image_file = tmp_path / "graph.png"
    image_file.write_bytes(b"\x89PNG")

    append_to_document("doc123", text="Description", image_path=image_file)

    mock_verify.assert_called_once_with("doc123")
    mock_text.assert_called_once_with("doc123", "Description")
    mock_image.assert_called_once_with("doc123", image_file)


@patch(f"{MODULE}.append_image")
@patch(f"{MODULE}.append_text")
@patch(f"{MODULE}._verify_is_document")
def test_append_to_document_text_only(mock_verify, mock_text, mock_image):
    append_to_document("doc123", text="Just text")

    mock_text.assert_called_once_with("doc123", "Just text")
    mock_image.assert_not_called()


@patch(f"{MODULE}.append_image")
@patch(f"{MODULE}.append_text")
@patch(f"{MODULE}._verify_is_document")
def test_append_to_document_image_only(mock_verify, mock_text, mock_image, tmp_path):
    image_file = tmp_path / "graph.png"
    image_file.write_bytes(b"\x89PNG")

    append_to_document("doc123", image_path=image_file)

    mock_text.assert_not_called()
    mock_image.assert_called_once_with("doc123", image_file)


@patch(f"{MODULE}.run_gws_json")
def test_append_to_document_non_document_rejected(mock_json):
    mock_json.return_value = {"mimeType": "application/vnd.google-apps.spreadsheet"}

    with pytest.raises(ValueError, match="only supported for Google Documents"):
        append_to_document("sheet123", text="text")
