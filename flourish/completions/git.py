"""Git command completion for Flourish."""

from prompt_toolkit.completion import Completion


def complete_git(current_word: str, words: list[str], word_index: int) -> list[Completion]:
    """Complete git commands and subcommands.

    Args:
        current_word: The current word being completed
        words: All words in the command line
        word_index: Index of the current word

    Returns:
        List of Completion objects
    """
    git_subcommands = [
        "add",
        "commit",
        "push",
        "pull",
        "status",
        "log",
        "branch",
        "checkout",
        "merge",
        "rebase",
        "stash",
        "diff",
        "show",
        "reset",
        "revert",
        "clone",
        "init",
        "remote",
        "fetch",
        "tag",
        "blame",
        "grep",
        "bisect",
        "cherry-pick",
        "reflog",
    ]

    completions = []

    if word_index == 1:
        # Completing git subcommand
        for cmd in git_subcommands:
            if cmd.startswith(current_word.lower()):
                start_pos = -len(current_word) if current_word else 0
                completions.append(
                    Completion(
                        cmd,
                        start_position=start_pos,
                        display=cmd,
                    )
                )
    elif word_index == 2:
        # Completing argument to git subcommand
        subcommand = words[1].lower() if len(words) > 1 else ""

        if subcommand in ["checkout", "branch", "switch"]:
            # Could complete branch names, but for now just return empty
            # In a full implementation, you'd run `git branch -a` to get branches
            pass
        elif subcommand in ["add", "restore", "rm"]:
            # Could complete file paths
            pass

    return completions
