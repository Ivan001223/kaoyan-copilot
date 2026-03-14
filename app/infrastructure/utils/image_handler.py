import base64
import io
import mimetypes
import re
from typing import List, Dict, Any, Optional, Tuple, Union

import numpy as np
import requests
from PIL import Image


def encode_image_to_base64(image: Union[str, Image.Image, bytes]) -> str:
    """Encode an image to base64 string.

    Args:
        image: The image to encode. Can be a file path, PIL Image, or bytes.

    Returns:
        The base64 encoded string of the image.
    """
    if isinstance(image, str):
        with open(image, "rb") as f:
            image_bytes = f.read()
        return base64.b64encode(image_bytes).decode("utf-8")
    elif isinstance(image, Image.Image):
        buffered = io.BytesIO()
        image.save(buffered, format=image.format or "PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    elif isinstance(image, bytes):
        return base64.b64encode(image).decode("utf-8")
    else:
        raise ValueError(f"Unsupported image type: {type(image)}")


def decode_image_from_base64(base64_str: str) -> Image.Image:
    """Decode a base64 string to PIL Image.

    Args:
        base64_str: The base64 encoded string of the image.

    Returns:
        The decoded PIL Image.
    """
    image_bytes = base64.b64decode(base64_str)
    return Image.open(io.BytesIO(image_bytes))


def resize_image(
    image: Union[str, Image.Image, bytes], max_size: Tuple[int, int] = (1024, 1024)
) -> Image.Image:
    """Resize an image to fit within max_size while maintaining aspect ratio.

    Args:
        image: The image to resize. Can be a file path, PIL Image, or bytes.
        max_size: The maximum size (width, height) of the resized image.

    Returns:
        The resized PIL Image.
    """
    if isinstance(image, str):
        image = Image.open(image)
    elif isinstance(image, bytes):
        image = Image.open(io.BytesIO(image))

    if image.width <= max_size[0] and image.height <= max_size[1]:
        return image


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
                    processed_content.append(item)
            else:
                processed_content.append(item)
        else:
            processed_content.append(item)
    return processed_content


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


    ratio = min(max_size[0] / image.width, max_size[1] / image.height)
    new_size = (int(image.width * ratio), int(image.height * ratio))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def crop_image(
    image: Union[str, Image.Image, bytes], box: Tuple[int, int, int, int]
) -> Image.Image:
    """Crop an image to the specified box.

    Args:
        image: The image to crop. Can be a file path, PIL Image, or bytes.
        box: The box to crop to (left, top, right, bottom).

    Returns:
        The cropped PIL Image.
    """
    if isinstance(image, str):
        image = Image.open(image)
    elif isinstance(image, bytes):
        image = Image.open(io.BytesIO(image))

    return image.crop(box)


def convert_image_format(
    image: Union[str, Image.Image, bytes], format: str = "PNG"
) -> bytes:
    """Convert an image to the specified format.

    Args:
        image: The image to convert. Can be a file path, PIL Image, or bytes.
        format: The target format (e.g., "PNG", "JPEG", "WEBP").

    Returns:
        The converted image as bytes.
    """
    if isinstance(image, str):
        image = Image.open(image)
    elif isinstance(image, bytes):
        image = Image.open(io.BytesIO(image))

    buffered = io.BytesIO()
    image.save(buffered, format=format)
    return buffered.getvalue()


def get_image_info(image: Union[str, Image.Image, bytes]) -> dict:
    """Get information about an image.

    Args:
        image: The image to get info from. Can be a file path, PIL Image, or bytes.

    Returns:
        A dictionary containing image information (width, height, format, mode).
    """
    if isinstance(image, str):
        image = Image.open(image)
    elif isinstance(image, bytes):
        image = Image.open(io.BytesIO(image))

    return {
        "width": image.width,
        "height": image.height,
        "format": image.format,
        "mode": image.mode,
    }


def is_valid_image(image: Union[str, Image.Image, bytes]) -> bool:
    """Check if an image is valid.

    Args:
        image: The image to check. Can be a file path, PIL Image, or bytes.

    Returns:
        True if the image is valid, False otherwise.
    """
    try:
        if isinstance(image, str):
            image = Image.open(image)
        elif isinstance(image, bytes):
            image = Image.open(io.BytesIO(image))
        image.load()
        return True
    except Exception:
        return False


def preprocess_image_for_ocr(image: Union[str, Image.Image, bytes]) -> Image.Image:
    """Preprocess an image for OCR.

    This function converts the image to grayscale and increases contrast.

    Args:
        image: The image to preprocess. Can be a file path, PIL Image, or bytes.

    Returns:
        The preprocessed PIL Image.
    """
    if isinstance(image, str):
        image = Image.open(image)
    elif isinstance(image, bytes):
        image = Image.open(io.BytesIO(image))

    # Convert to grayscale
    if image.mode != "L":
        image = image.convert("L")

    # Increase contrast
    from PIL import ImageEnhance

    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)

    return image
