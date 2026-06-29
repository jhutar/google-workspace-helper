import json
import logging
from pathlib import Path

from google_workspace_helper.gws_runner import (
    run_gws,
    run_gws_json,
    run_gws_upload,
)

logger = logging.getLogger("google_workspace_helper")

MIME_DOCUMENT = "application/vnd.google-apps.document"


def _get_user_domain() -> str:
    data = run_gws_json("drive", "about", "get", "--params", '{"fields": "user"}')
    email = data.get("user", {}).get("emailAddress", "")
    if "@" not in email:
        raise RuntimeError(f"Could not determine domain from email: {email}")
    return email.split("@", 1)[1]


def _verify_is_document(file_id: str) -> None:
    params = json.dumps({"fileId": file_id, "fields": "mimeType"})
    data = run_gws_json("drive", "files", "get", "--params", params)
    mime_type = data.get("mimeType", "")
    if mime_type != MIME_DOCUMENT:
        raise ValueError(
            f"Append is only supported for Google Documents, "
            f"but file has type: {mime_type}"
        )


def append_text(file_id: str, text: str) -> None:
    logger.debug("Appending text to document file_id=%s", file_id)
    body = {
        "requests": [
            {
                "insertText": {
                    "endOfSegmentLocation": {"segmentId": ""},
                    "text": "\n" + text,
                }
            }
        ]
    }
    params = json.dumps({"documentId": file_id})
    run_gws_json(
        "docs", "documents", "batchUpdate", "--params", params, json_body=body
    )


def append_image(file_id: str, image_path: Path) -> None:
    logger.debug(
        "Appending image %s to document file_id=%s", image_path, file_id
    )

    domain = _get_user_domain()

    content_type_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
    }
    suffix = image_path.suffix.lower()
    content_type = content_type_map.get(suffix)

    upload_response = run_gws_upload(
        "drive",
        "files",
        "create",
        upload_path=image_path,
        upload_content_type=content_type,
    )
    uploaded_file_id = upload_response["id"]
    logger.debug("Uploaded image as Drive file_id=%s", uploaded_file_id)

    try:
        perm_params = json.dumps({"fileId": uploaded_file_id})
        perm_body = {"role": "reader", "type": "domain", "domain": domain}
        run_gws_json(
            "drive", "permissions", "create",
            "--params", perm_params,
            json_body=perm_body,
        )
        logger.debug("Set domain reader permission on %s", uploaded_file_id)

        meta_params = json.dumps(
            {"fileId": uploaded_file_id, "fields": "webContentLink"}
        )
        meta = run_gws_json("drive", "files", "get", "--params", meta_params)
        web_content_link = meta.get("webContentLink")
        if not web_content_link:
            raise RuntimeError(
                "Drive file metadata did not include webContentLink"
            )
        logger.debug("Got webContentLink: %s", web_content_link)

        insert_body = {
            "requests": [
                {
                    "insertInlineImage": {
                        "endOfSegmentLocation": {"segmentId": ""},
                        "uri": web_content_link,
                    }
                }
            ]
        }
        doc_params = json.dumps({"documentId": file_id})
        run_gws_json(
            "docs", "documents", "batchUpdate",
            "--params", doc_params,
            json_body=insert_body,
        )
        logger.debug("Inserted image into document %s", file_id)
    finally:
        del_params = json.dumps({"fileId": uploaded_file_id})
        run_gws("drive", "files", "delete", "--params", del_params)
        logger.debug("Deleted temporary Drive file %s", uploaded_file_id)


def append_to_document(
    file_id: str,
    text: str | None = None,
    image_path: Path | None = None,
) -> None:
    _verify_is_document(file_id)

    if text:
        append_text(file_id, text)
    if image_path:
        append_image(file_id, image_path)
