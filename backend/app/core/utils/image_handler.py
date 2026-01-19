import base64
import mimetypes
import requests
from typing import List, Dict, Any, Union

def is_local_url(url: str) -> bool:
    """Check if the URL points to a local server."""
    return url.startswith('http://localhost') or url.startswith('http://127.0.0.1')

def convert_url_to_base64(url: str) -> str:
    """
    Fetches an image from a URL and converts it to a base64 data URI.
    Useful for passing local images to cloud LLMs.
    """
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            mime_type = mimetypes.guess_type(url)[0] or 'image/jpeg'
            b64_data = base64.b64encode(resp.content).decode('utf-8')
            return f"data:{mime_type};base64,{b64_data}"
    except Exception as e:
        print(f"Error converting image to base64: {e}")
    return None

def process_multimodal_content(raw_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Processes a list of content items (multimodal message), converting local image URLs
    to base64 data URIs where necessary.
    """
    processed_content = []
    for item in raw_content:
        if item.get('type') == 'image_url':
            url = item['image_url']['url']
            if is_local_url(url):
                data_uri = convert_url_to_base64(url)
                if data_uri:
                    processed_content.append({
                        "type": "image_url",
                        "image_url": {"url": data_uri}
                    })
                else:
                    # Fallback: keep original (might fail)
                    processed_content.append(item)
            else:
                processed_content.append(item)
        else:
            processed_content.append(item)
    return processed_content
