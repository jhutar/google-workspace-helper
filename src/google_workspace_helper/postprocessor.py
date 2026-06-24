import os
import re
import base64
from pathlib import Path
from typing import Tuple, List

# Regular expression to find Markdown images with base64 URIs or raw base64 data URIs
IMAGE_RE = re.compile(r'data:image/(?P<ext>[a-zA-Z0-9+-.]+);base64,(?P<data>[a-zA-Z0-9+/= \r\n]+)')

def post_process_markdown(markdown_content: str, file_id: str) -> str:
    """Extracts inline base64 images, decodes them to /tmp/<file_id>/, and replaces the links."""
    temp_dir = Path(f"/tmp/{file_id}")
    image_index = 1
    
    def replace_match(match: re.Match) -> str:
        nonlocal image_index
        
        # Ensure temporary directory exists only when at least one image is processed
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        ext = match.group("ext")
        # Normalize extension: jpeg -> jpg
        if ext.lower() == "jpeg":
            ext = "jpg"
            
        raw_data = match.group("data").strip().replace("\r", "").replace("\n", "").replace(" ", "")
        
        try:
            decoded_bytes = base64.b64decode(raw_data)
        except Exception as e:
            raise ValueError(f"Error: Failed to decode base64 image at index {image_index}: {e}") from e
            
        file_name = f"image_{image_index}.{ext}"
        file_path = temp_dir / file_name
        
        # Write decoded binary data to local file
        file_path.write_bytes(decoded_bytes)
        
        # Return the clean local relative path
        local_ref = f"/tmp/{file_id}/{file_name}"
        image_index += 1
        return local_ref

    # Replace matches in markdown content
    processed_content = IMAGE_RE.sub(replace_match, markdown_content)
    return processed_content
