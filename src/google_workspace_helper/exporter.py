import logging
import shutil
import subprocess
import json
import tempfile
import zipfile
import re
import xml.etree.ElementTree as ET  # nosec B405
from pathlib import Path

logger = logging.getLogger("google_workspace_helper")

MIME_SPREADSHEET = "application/vnd.google-apps.spreadsheet"
MIME_PRESENTATION = "application/vnd.google-apps.presentation"
MIME_DOCUMENT = "application/vnd.google-apps.document"


def verify_gws_installed() -> None:
    if not shutil.which("gws"):
        raise FileNotFoundError(
            "Error: gws CLI tool not found in system PATH. Please install it first."
        )


def verify_pandoc_installed() -> None:
    if not shutil.which("pandoc"):
        raise FileNotFoundError(
            "Error: pandoc is not installed. Please install pandoc to convert "
            "presentations to Markdown. Visit https://pandoc.org/installing.html"
        )


def get_file_mime_type(file_id: str) -> str:
    verify_gws_installed()
    params_json = json.dumps({"fileId": file_id, "fields": "mimeType"})
    command = ["gws", "drive", "files", "get", "--params", params_json]
    logger.debug("Fetching mime type for file_id=%s", file_id)
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        mime_type = data.get("mimeType", "")
        logger.debug("Detected mime type: %s", mime_type)
        return mime_type
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        raise RuntimeError(f"Error fetching file metadata: {error_msg}") from e
    except (json.JSONDecodeError, KeyError) as e:
        raise RuntimeError(f"Error parsing file metadata response: {e}") from e


def export_file(file_id: str, mime_type: str = "text/markdown") -> str:
    verify_gws_installed()
    with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
        output_file = Path(tmp_dir) / f"{file_id}.export"
        params_dict = {"fileId": file_id, "mimeType": mime_type}
        params_json = json.dumps(params_dict)
        command = [
            "gws",
            "drive",
            "files",
            "export",
            "--params",
            params_json,
            "--output",
            str(output_file),
        ]
        logger.debug(
            "Exporting file_id=%s with mime_type=%s via tempfile", file_id, mime_type
        )
        try:
            # Capture output to prevent gws logs or stdout JSON from leaking to our processes
            subprocess.run(command, capture_output=True, check=True)
            if output_file.exists():
                return output_file.read_text(encoding="utf-8")
            else:
                raise FileNotFoundError(
                    f"Error: Export file was not created by gws: {output_file}"
                )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode().strip() if e.stderr else str(e)
            raise RuntimeError(f"Error executing gws export: {error_msg}") from e


def export_spreadsheet_as_csv(file_id: str) -> str:
    verify_gws_installed()
    logger.debug("Exporting spreadsheet file_id=%s as CSV", file_id)
    logger.warning(
        "Only the first sheet of the spreadsheet will be exported. "
        "Multi-sheet export is not supported."
    )
    return export_file(file_id, mime_type="text/csv")


def _p_match_text_nodes(p_elem: ET.Element) -> list:
    """Recursively finds all text node elements under drawingml paragraph."""
    text_nodes = []
    for elem in p_elem.iter():
        if elem.tag.endswith("}t") or elem.tag == "t":
            text_nodes.append(elem)
    return text_nodes


def extract_html_from_pptx(pptx_path: Path) -> str:
    html_slides = []
    with zipfile.ZipFile(pptx_path, "r") as zip_ref:
        # Find slide files
        slide_files = [
            f for f in zip_ref.namelist() if re.match(r"^ppt/slides/slide\d+\.xml$", f)
        ]
        # Sort sequentially by slide numbers extracted from filenames
        slide_files.sort(key=lambda f: int(re.search(r"\d+", f).group()))

        for slide_file in slide_files:
            slide_xml = zip_ref.read(slide_file)
            root = ET.fromstring(slide_xml)  # nosec B314

            slide_paragraphs = []
            for p_elem in root.iter():
                if p_elem.tag.endswith("}p") or p_elem.tag == "p":
                    texts = []
                    for t_node in _p_match_text_nodes(p_elem):
                        if t_node.text:
                            texts.append(t_node.text)
                    para_text = "".join(texts).strip()
                    if para_text:
                        slide_paragraphs.append(para_text)

            if slide_paragraphs:
                title = slide_paragraphs[0]
                body = slide_paragraphs[1:]

                slide_html = f"<h2>{title}</h2>\n"
                if body:
                    slide_html += "<ul>\n"
                    for para in body:
                        slide_html += f"  <li>{para}</li>\n"
                    slide_html += "</ul>\n"
                html_slides.append(slide_html)
            else:
                html_slides.append("<h2>Slide</h2>\n<p><i>Empty Slide</i></p>\n")

    return "\n<hr />\n".join(html_slides)


def export_presentation_as_markdown(file_id: str) -> str:
    verify_gws_installed()
    verify_pandoc_installed()
    logger.debug("Exporting presentation file_id=%s via PPTX+pandoc", file_id)

    pptx_mime = (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
        pptx_path = Path(tmp_dir) / f"{file_id}.pptx"
        params_json = json.dumps({"fileId": file_id, "mimeType": pptx_mime})
        command = [
            "gws",
            "drive",
            "files",
            "export",
            "--params",
            params_json,
            "--output",
            str(pptx_path),
        ]

        try:
            subprocess.run(command, capture_output=True, check=True)
            if not pptx_path.exists() or pptx_path.stat().st_size == 0:
                raise ValueError(
                    "Error: gws export command succeeded but PPTX file is empty or missing."
                )
            logger.debug("Downloaded PPTX to %s", pptx_path)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode().strip() if e.stderr else str(e)
            raise RuntimeError(f"Error downloading presentation: {error_msg}") from e

        # Extract slide structure to clean HTML
        try:
            html_content = extract_html_from_pptx(pptx_path)
        except Exception as e:
            raise RuntimeError(f"Error parsing PPTX structure: {e}") from e

        pandoc_cmd = [
            "pandoc",
            "-f",
            "html",
            "-t",
            "markdown",
        ]
        try:
            pandoc_result = subprocess.run(
                pandoc_cmd,
                input=html_content,
                capture_output=True,
                text=True,
                check=True,
            )
            logger.debug("Pandoc conversion complete for file_id=%s", file_id)
            return pandoc_result.stdout
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            raise RuntimeError(
                f"Error converting presentation with pandoc: {error_msg}"
            ) from e
