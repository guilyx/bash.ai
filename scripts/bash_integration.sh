#!/bin/bash
# Bash integration script for Flouri
# Add this to your ~/.bashrc or ~/.zshrc

# Function to provide AI-powered command suggestions
_flouri_suggest() {
    local command="$1"
    if [ -z "$command" ]; then
        return
    fi

    # Check if flouri is available
    if ! command -v flouri &> /dev/null; then
        return
    fi

    # Get AI suggestion (non-blocking, runs in background)
    (flouri "Suggest the next command after: $command" 2>/dev/null) &
}

# Function to enhance command execution with AI
_flouri_enhance() {
    local last_command="$1"
    local exit_code="$2"

    # If command failed, ask AI for help
    if [ "$exit_code" -ne 0 ]; then
        if command -v flouri &> /dev/null; then
            echo ""
            echo "💡 AI Suggestion:"
            flouri "The command '$last_command' failed with exit code $exit_code. What might be wrong and how to fix it?" 2>/dev/null | head -5
            echo ""
        fi
    fi
}

# Hook into command execution (if supported)
if [ -n "$BASH_VERSION" ]; then
    # Bash-specific hooks
    trap '_flouri_enhance "$BASH_COMMAND" "$?"' DEBUG 2>/dev/null || true
fi

# Create convenient alias
alias ai='flouri'

# Auto-completion helper
_flouri_complete() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    if [ "$COMP_CWORD" -eq 1 ]; then
        COMPREPLY=($(compgen -W "--allowlist --blacklist --help --version" -- "$cur"))
    fi
}

# Register completion (if available)
if command -v complete &> /dev/null; then
    complete -F _flouri_complete flouri
fi

echo "Flouri integration loaded. Use 'flouri' or 'ai' command."
