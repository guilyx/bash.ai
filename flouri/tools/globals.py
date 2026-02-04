"""Shared global variables for tools."""

import os

# Global variable for working directory
GLOBAL_CWD = os.getcwd()  # Default to current directory

# Global variables for allowlist/blacklist
GLOBAL_ALLOWLIST: list[str] | None = None
GLOBAL_BLACKLIST: list[str] | None = None
