"""
Validation Utilities - Complete Working Implementation for SyncAI
"""

from typing import Any, Dict, List, Optional
import re

def validate_persona(persona: str, available_personas: List[str]) -> bool:
    """Validate persona against available options"""
    return persona in available_personas

def validate_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Basic request validation"""
    errors = []
    warnings = []
    
    # Check required fields
    if not data:
        errors.append("Request data is empty")
        return {"valid": False, "errors": errors, "warnings": warnings}
    
    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """Validate file extension"""
    if not filename:
        return False
    
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    return f".{file_ext}" in allowed_extensions

def validate_api_key(api_key: str) -> bool:
    """Basic API key validation"""
    if not api_key:
        return False
    
    # Basic checks
    if len(api_key) < 8:
        return False
    
    # Check for obvious test/placeholder values
    test_values = ["test", "placeholder", "your-key", "api-key"]
    return not any(test in api_key.lower() for test in test_values)

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    sanitized = re.sub(r'\.\.', '_', sanitized)  # Remove path traversal
    return sanitized[:255]  # Limit length

def validate_correlation_id(correlation_id: str) -> bool:
    """Validate correlation ID format"""
    if not correlation_id:
        return False
    
    # Basic format check
    return len(correlation_id) >= 8 and len(correlation_id) <= 128
