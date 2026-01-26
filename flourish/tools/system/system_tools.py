"""System information tools."""

from typing import Any

from ...logging import log_tool_call


def get_current_datetime() -> dict[str, Any]:
    """
    Get the current date and time.

    This tool helps the agent understand the current time context, which is useful for
    time-sensitive operations, scheduling, or understanding when events occurred.

    Returns:
        A dictionary with current date, time, timezone, and ISO format timestamp.
    """
    from datetime import datetime, timezone

    # Use timezone.utc for Python 3.10+ compatibility (UTC alias requires 3.11+)
    now = datetime.now(timezone.utc)  # noqa: UP017
    local_now = datetime.now()

    result: dict[str, Any] = {
        "status": "success",
        "iso_timestamp": now.isoformat(),
        "local_datetime": local_now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": local_now.strftime("%Y-%m-%d"),
        "time": local_now.strftime("%H:%M:%S"),
        "timezone": str(local_now.astimezone().tzinfo) if local_now.tzinfo else "local",
        "utc_datetime": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    log_tool_call("get_current_datetime", {}, result, success=True)
    return result
