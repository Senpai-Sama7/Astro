"""
Helper utilities for data processing and validation
"""
import json
import re
from typing import Dict, Any, List, Optional
import hashlib

def sanitize_filename(filename: str) -> str:
    """Sanitize a string to be safe for use as a filename"""
    return re.sub(r'[^\w\-_\. ]', '_', filename)

def calculate_checksum(data: Any) -> str:
    """Calculate SHA-256 checksum of a dictionary or string"""
    if isinstance(data, dict):
        content = json.dumps(data, sort_keys=True)
    else:
        content = str(data)
    return hashlib.sha256(content.encode()).hexdigest()

def validate_json_schema(data: Dict, schema: Dict[str, type]) -> bool:
    """
    Validate that data conforms to a simple type schema.
    
    Args:
        data: Dictionary to validate
        schema: Dict mapping required keys to their expected Python types
        
    Returns:
        True if all required keys exist with correct types, False otherwise
        
    Example:
        >>> schema = {"name": str, "age": int}
        >>> validate_json_schema({"name": "Alice", "age": 30}, schema)
        True
        >>> validate_json_schema({"name": "Alice"}, schema)
        False
    
    Note:
        For complex JSON Schema validation (draft-07, etc.), consider using
        the 'jsonschema' library: pip install jsonschema
    """
    for key, expected_type in schema.items():
        if key not in data:
            return False
        if not isinstance(data[key], expected_type):
            return False
    return True

def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to max_length while preserving whole words if possible"""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + '...'
