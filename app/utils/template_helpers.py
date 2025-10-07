from typing import Optional, Dict, Any


def first_name_from_user(user: Optional[Dict[str, Any]]) -> str:
    """Extract the first name from user's display_name or email."""
    if not user:
        return ""
    value = (user.get("display_name") or user.get("email") or "").strip()
    if not value:
        return ""
    parts = value.split()
    return parts[0] if parts else value


