import pytest
import os
import shutil
from pathlib import Path
from google_workspace_helper.postprocessor import post_process_markdown

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
