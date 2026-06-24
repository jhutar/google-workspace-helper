import os
import shutil
from pathlib import Path
from google_workspace_helper.postprocessor import (
    post_process_markdown,
    csv_to_markdown_table,
)


def test_post_process_markdown_with_images():
    file_id = "test_doc_id"
    # Small valid base64 PNG data: single transparent pixel
    base64_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    raw_markdown = f"""
# Test Document
Here is an image:
![my image](data:image/png;base64,{base64_png})

And another JPEG image:
![another](data:image/jpeg;base64,{base64_png})
"""

    try:
        clean_markdown = post_process_markdown(raw_markdown, file_id)

        # Verify markdown replacements
        assert "data:image/png;base64" not in clean_markdown
        assert "data:image/jpeg;base64" not in clean_markdown
        assert "![my image](/tmp/test_doc_id/image_1.png)" in clean_markdown
        assert "![another](/tmp/test_doc_id/image_2.jpg)" in clean_markdown

        # Verify local file generation
        img1_path = Path("/tmp/test_doc_id/image_1.png")
        img2_path = Path("/tmp/test_doc_id/image_2.jpg")

        assert img1_path.exists()
        assert img2_path.exists()
        assert len(img1_path.read_bytes()) > 0
    finally:
        # Cleanup
        shutil.rmtree("/tmp/test_doc_id", ignore_errors=True)


def test_post_process_markdown_no_images():
    file_id = "test_doc_id_no_images"
    raw_markdown = "# Simple document\nNo images present."
    clean_markdown = post_process_markdown(raw_markdown, file_id)

    assert clean_markdown == raw_markdown
    assert not os.path.exists(f"/tmp/{file_id}")


def test_csv_to_markdown_table_basic():
    csv_content = "Name,Age,City\nAlice,30,Prague\nBob,25,Brno\n"
    result = csv_to_markdown_table(csv_content)
    expected = (
        "| Name | Age | City |\n"
        "| --- | --- | --- |\n"
        "| Alice | 30 | Prague |\n"
        "| Bob | 25 | Brno |\n"
    )
    assert result == expected


def test_csv_to_markdown_table_pipe_escaping():
    csv_content = 'Header1,Header2\n"value|with|pipes",normal\n'
    result = csv_to_markdown_table(csv_content)
    assert "value\\|with\\|pipes" in result
    assert "normal" in result


def test_csv_to_markdown_table_empty():
    assert csv_to_markdown_table("") == ""


def test_csv_to_markdown_table_header_only():
    csv_content = "Col1,Col2,Col3\n"
    result = csv_to_markdown_table(csv_content)
    assert "| Col1 | Col2 | Col3 |" in result
    assert "| --- | --- | --- |" in result
    lines = result.strip().split("\n")
    assert len(lines) == 2


def test_csv_to_markdown_table_uneven_rows():
    csv_content = "A,B,C\n1,2\n4,5,6\n"
    result = csv_to_markdown_table(csv_content)
    lines = result.strip().split("\n")
    assert len(lines) == 4
    assert lines[2] == "| 1 | 2 |  |"
