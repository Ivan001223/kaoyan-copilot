import json
import re
from typing import Any, Dict, List, Union


def parse_json(
    content: Union[str, bytes],
    default: Any = None,
    strict: bool = False,
) -> Any:
    """Parse JSON from content that may contain extra text or formatting.

    This function handles the following cases:
    1. Pure JSON string
    2. JSON mixed with explanatory text
    3. JSON in Markdown code blocks (```json or ```)
    4. Content with <think> tags

    Args:
        content: The content to parse.
        default: The default value to return if parsing fails.
        strict: If True, raise an exception on parse failure instead of returning default.

    Returns:
        The parsed JSON object, or default if parsing fails and strict is False.

    Raises:
        ValueError: If strict is True and parsing fails.
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8")

    content = re.sub(r"<think>.*?
</think>", "", content, flags=re.DOTALL)

    content = re.sub(r"```json\s*", "", content)
    content = re.sub(r"```", "", content)

    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                json_str_fixed = json_str.replace("\\", "\\\\")
                try:
                    return json.loads(json_str_fixed)
                except:
                    pass

        match_list = re.search(r"\[.*\]", content, re.DOTALL)
        if match_list:
            json_str = match_list.group(0)
            try:
                return json.loads(json_str)
            except:
                pass

        if strict:
            raise ValueError(f"Could not parse JSON from content: {content[:100]}...")

        return default


def extract_json_objects(
    content: Union[str, bytes],
) -> List[Dict[str, Any]]:
    """Extract all JSON objects from content.

    This function finds all JSON objects (dict or list) in the content
    and returns them as a list.

    Args:
        content: The content to extract JSON objects from.

    Returns:
        A list of extracted JSON objects.
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8")

    content = re.sub(r"<think>.*?
</think>", "", content, flags=re.DOTALL)

    objects = []

    for match in re.finditer(r"\{.*?\}", content, re.DOTALL):
        json_str = match.group(0)
        try:
            obj = json.loads(json_str)
            objects.append(obj)
        except:
            pass

    for match in re.finditer(r"\[.*?\]", content, re.DOTALL):
        json_str = match.group(0)
        try:
            obj = json.loads(json_str)
            if isinstance(obj, list):
                objects.append(obj)
        except:
            pass

    return objects


def to_json_string(
    obj: Any,
    indent: Optional[int] = None,
    ensure_ascii: bool = False,
) -> str:
    """Convert an object to a JSON string.

    Args:
        obj: The object to convert.
        indent: The indentation level for pretty printing.
        ensure_ascii: If True, escape non-ASCII characters.

    Returns:
        The JSON string representation of the object.
    """
    return json.dumps(obj, indent=indent, ensure_ascii=ensure_ascii)


def format_json(
    content: Union[str, bytes],
    indent: int = 2,
    ensure_ascii: bool = False,
) -> str:
    """Format content as a pretty JSON string.

    This function first parses the content as JSON, then formats it
    as a pretty JSON string.

    Args:
        content: The content to format.
        indent: The indentation level for pretty printing.
        ensure_ascii: If True, escape non-ASCII characters.

    Returns:
        The formatted JSON string.

    Raises:
        ValueError: If the content cannot be parsed as JSON.
    """
    obj = parse_json(content, strict=True)
    return to_json_string(obj, indent=indent, ensure_ascii=ensure_ascii)
