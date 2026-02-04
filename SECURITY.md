# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Considerations

### Command Execution

**⚠️ IMPORTANT**: The `agent` command can execute terminal commands on your system. This is a powerful feature but comes with security risks.

#### Best Practices

1. **Use Allowlists**: Always use the `--allowlist` flag in production or sensitive environments:
   ```bash
   flouri agent --allowlist "ls,cd,git" "Safe task"
   ```

2. **Use Blacklists**: Prevent dangerous commands:
   ```bash
   flouri agent --blacklist "rm,dd,format,mkfs" "Task"
   ```

3. **Review Before Execution**: The agent will explain what it plans to do. Review carefully before confirming.

4. **API Key Security**:
   - Never commit your `.env` file or API keys to version control
   - Use environment variables or secure secret management
   - Rotate API keys regularly

5. **Permissions**: The agent runs with the same permissions as your user account. Don't run as root unless absolutely necessary.

### Dangerous Commands

The following commands are particularly dangerous and should be blacklisted by default:
- `rm -rf` (recursive deletion)
- `dd` (disk operations)
- `format` / `mkfs` (filesystem operations)
- `chmod 777` (permission changes)
- `sudo` commands (elevated privileges)
- Network commands that could expose your system

### Reporting a Vulnerability

If you discover a security vulnerability, please **DO NOT** open a public issue. Instead:

1. Email the maintainers directly (if contact info is available)
2. Or create a private security advisory on GitHub
3. Provide:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if you have one)

We will respond within 48 hours and work with you to address the issue.

## Security Features

- Command allowlist/blacklist enforcement
- API key management via environment variables
- Security-focused agent instructions
- No automatic execution of destructive commands

## Limitations

- The agent uses Python code execution (via BuiltInCodeExecutor) which runs shell commands
- There is no sandboxing by default - commands run in your actual environment
- The allowlist/blacklist is enforced through agent instructions, not system-level restrictions

## Future Security Enhancements

- [ ] System-level command filtering
- [ ] Sandboxed execution environment
- [ ] Command confirmation prompts
- [ ] Audit logging of executed commands
- [ ] Rate limiting for API calls
