MAX_OUTPUT_CHARS = 8000


def truncate_output(text: str, max_chars: int = MAX_OUTPUT_CHARS) -> str:
    """Truncate text to max_chars, appending an explicit truncation notice if cut."""
    if len(text) <= max_chars:
        return text
    omitted = len(text) - max_chars
    return text[:max_chars] + f"\n... [truncated, {omitted} more characters omitted]"


class ToolError(Exception):
    """Raised for tool input errors that should be reported back as a tool result."""
