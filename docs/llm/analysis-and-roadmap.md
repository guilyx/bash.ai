# LLM Integration: Critical Analysis and Roadmap

This document is an objective, critical review of Flouri’s LLM/agent integration. It does not aim to be agreeable; it calls out gaps, inconsistencies, and design flaws so that improvements can be prioritized on evidence.

---

## 1. Current State: What the Code Actually Does

### 1.1 Stack (Factual)

| Layer | Technology | Role |
|-------|------------|------|
| Orchestration | Google ADK | Agent loop, tool dispatch, session, streaming |
| Model access | LiteLLM | Unified API for multiple providers |
| Agent | `LlmAgent` + `BuiltInPlanner` | Single agent; thinking budget 15000, `include_thoughts=True` (hardcoded) |
| Tools | Skill registry | Bash, config, history, system, ros2, tool_manager |
| Runner | Custom async/sync wrappers | New session per request; event loop over ADK events |

### 1.2 Data Flow (Factual)

1. User input → runner.
2. Runner creates a **new** `InMemorySessionService`, **new** session, **new** agent, and **new** `Runner` instance for **every** request.
3. One user message is sent. No prior conversation is passed.
4. Events are iterated; parts are inspected for `executable_code`, `code_execution_result`, and `text`. Response is assembled by concatenating and deduplicating parts.
5. Response is logged and returned (or streamed in the live path).

There is no multi-turn conversation in the current implementation. Every call is single-turn from the model’s perspective.

---

## 2. Critical Review

### 2.1 Documentation vs Implementation

**Architecture doc (`docs/architecture.md`) is wrong on security and confirmation.**

- It states: “If the command is not in the allowlist, it triggers a confirmation flow” and “If confirmation is needed, the system (via `ToolContext.request_confirmation`) prompts the user.”
- **In code**: There is no confirmation flow. `execute_bash` never calls `ToolContext.request_confirmation`. The agent instruction explicitly says “Never ask for confirmation - the system handles security automatically.” Commands not on the allowlist are **automatically added to the allowlist** and executed (see `bash_tools.execute_bash`: if not in allowlist, append to `GLOBAL_ALLOWLIST` and optionally call `ConfigManager.add_to_allowlist`, then proceed). So the architecture describes a confirmation step that does not exist and contradicts the implemented behavior.
- Either the doc was written for a different design or it was never updated when the “auto-add and run” behavior was introduced. Either way, it is misleading for anyone evaluating or hardening security.

**Conclusion**: The security model is not “allowlist + confirmation for unknown commands.” It is “allowlist + blacklist; unknown commands are auto-added to the allowlist and run.” That is a material difference and must be documented correctly.

---

### 2.2 Agent Instruction and Context

**The model is not given the allowlist or blacklist.**

- `build_agent_instruction()` returns a static string. It mentions “allowlist” and “blacklist” and tells the agent to use `is_in_allowlist` and `is_in_blacklist` to check. It does **not** inject the actual lists (e.g. “Allowed: ls, cd, pwd. Blocked: rm, dd.”). The lists are only used when building the tool set (`get_bash_tools(allowlist=..., blacklist=...)`) and enforced inside `execute_bash`.
- So the model has no direct view of what is allowed or blocked. To know, it must call tools. That costs extra turns and tokens and is easy for the model to skip or get wrong. There is no good reason not to put the current lists into the system prompt for every request.

**No runtime context is injected.**

- The instruction does not include: current working directory, git branch, last N commands, or any project-specific context. So the model cannot say “in this directory” or “given your last command” without the user re-stating it or the model calling tools (e.g. `get_user`, history tools). That makes multi-step or context-dependent requests brittle and verbose.

**Thinking budget and inclusion of thoughts are hardcoded.**

- `ThinkingConfig(thinking_budget=15000, include_thoughts=True)` is fixed in `agents.py`. Users cannot reduce cost or turn off thought inclusion without changing code. Not exposing these in config or env is a product and cost-control gap.

**Conclusion**: The prompt is minimal and underspecified. It relies on the model to infer security rules and context by calling tools instead of making the environment explicit in the instruction. That increases latency, cost, and the chance of the model misbehaving or ignoring checks.

---

### 2.3 Session and Multi-Turn

**There is no session continuity.**

- Each call to `run_agent` or `run_agent_live` creates a new `InMemorySessionService()` and a new session. The runner does not accept or persist a conversation history. So “list files” followed by “open the biggest one” is two independent single-turn calls; the second request has no access to the first unless the user repeats context or the model calls a history tool.
- The TUI does not maintain a single long-lived session across `?` requests. Each `handle_ai_request` is a new runner invocation with no prior turns. So the product does not support real multi-turn conversation in the sense of “the model sees the previous exchange.”

**Conclusion**: The system is single-turn by design in the runner. Any roadmap that promises “conversation” or “context across turns” requires a different session and history design, not small tweaks.

---

### 2.4 Runner Design and Duplication

**Event-handling logic is duplicated and brittle.**

- `run_agent` and `run_agent_live` each implement their own loop over `event.content.parts`, with nearly identical handling of `executable_code`, `code_execution_result`, and `text`. The only differences are streaming callbacks and how `final_response_text` and `output_parts` are merged at the end. Any fix or new part type (e.g. a new ADK event shape) must be applied in two places. This is a maintenance and bug risk.

**Response assembly is ad hoc.**

- Deduplication is done with a set over string parts. Order is preserved, but the logic for “what is the final answer” differs: in `run_agent`, `final_response_text` is tracked from `event.is_final_response()` and then merged with `output_parts`; in `run_agent_live` there is no `is_final_response()` check, and the merge order is different. So the two code paths can produce different outputs for the same logical response. There is no single, tested contract for “how we turn events into one response string.”

**Exceptions are flattened.**

- The runner catches `Exception` and re-raises `RuntimeError(f"Error during agent run: {e}")`. So specific errors (e.g. auth, rate limit, timeout) are lost to the caller. The UI and any retry or fallback logic cannot distinguish failure modes.

**Conclusion**: The runner is the core of the LLM integration but is under-specified and duplicated. It should be refactored so that event handling and response assembly live in one place and so that errors and response shape are well-defined.

---

### 2.5 TUI and Streaming

**The TUI does not use streaming.**

- The TUI imports and calls `run_agent` (the non-streaming path). So the user sees a spinner until the full response is ready. `run_agent_live` and `run_agent_live_sync` exist and are used by the CLI `--stream` path but are not used by the TUI. So the main interactive UX does not benefit from streaming; long agent runs feel like a black box.

**Conclusion**: Streaming is implemented for CLI but not for the primary interactive interface. That is a UX and consistency gap.

---

### 2.6 Security Model (Implementation)

**Auto-add to allowlist is a policy choice, not a given.**

- The instruction says “Commands not in allowlist are automatically added and executed.” The code does exactly that. So by default, any command the model chooses (that is not blacklisted) is added to the allowlist and run. There is no user confirmation, no “high-risk” subset, and no read-only mode. For a tool that can run arbitrary shell commands, that is a deliberate and risky default. The architecture doc’s claim that “confirmation” is used is false and obscures this.

**Blacklist is the only hard barrier.**

- The only commands that are always blocked are those on the blacklist. Everything else is allowed after auto-add. So the security story is “blacklist + trust the model.” There is no defense in depth (e.g. confirm before first use of `rm`, `dd`, or similar).

**Conclusion**: The security model should be described accurately: no confirmation for unknown commands; allowlist is extended automatically. If the project wants a stricter or configurable policy, that requires new code and config, not doc edits alone.

---

### 2.7 Observability and Operability

**No request or trace identity.**

- There is no trace id or request id passed through the runner and into logs. Correlating a user-visible failure with a specific log line or tool call requires timestamps and guesswork.

**No token or cost visibility.**

- The runner does not capture or log token usage. LiteLLM and providers often expose this, but Flouri does not surface it. So users and operators cannot see per-request or per-session cost.

**Tool calls are logged but not structured for analysis.**

- `log_tool_call` writes tool name, parameters, result, success, and duration. That is useful but not sufficient for systematic analysis (e.g. “which tools are called most,” “what is the distribution of failures”). There is no schema or pipeline for analytics.

**Conclusion**: The integration is hard to debug and impossible to cost-manage from within the product. Any serious use (especially with expensive models or thinking) will run into this.

---

### 2.8 Tool Set and Agent Behavior

**Large, flat tool set.**

- The agent receives all tools from the enabled skills (bash, config, history, system, ros2, tool_manager). There are many tools; the instruction does not group them or tell the model when to prefer one over another. So the model may over-use or under-use tools (e.g. calling history tools when the user did not ask about history, or forgetting to call them when context would help). Optional or scoped tool sets (e.g. “no ROS2 unless requested”) are not exposed in the instruction.

**get_user is expensive and can fail.**

- `get_user()` calls `execute_bash` three times (whoami, echo $HOME, pwd). Each call can trigger allowlist logic and subprocess. If any of these are blocked or fail, the result is partial. The instruction does not say “prefer get_user for user context” vs “run individual commands,” so the model may duplicate work or ignore get_user.

**Conclusion**: Tool design and instruction design are not aligned to minimize wasted calls or to make the “right” tool obvious. This can hurt latency and cost.

---

### 2.9 Testing and Maintainability

**Runner is not integration-tested.**

- The runner contains the core event-handling and response-assembly logic but is excluded from coverage (or only lightly tested). There are no tests that run a full agent loop with a mocked or canned model and assert that events are turned into the expected response shape. So regressions in event handling or in ADK API changes are easy to introduce.

**No prompt or instruction tests.**

- Changes to `build_agent_instruction()` are not validated by tests. There are no golden prompts or regression checks. So wording changes that weaken security or context can land unnoticed.

**Conclusion**: The most critical path (runner + instruction) is the least tested. That increases the risk of breakage and of security/UX regressions.

---

## 3. Summary of Critical Findings

| Area | Finding |
|------|---------|
| Docs | Architecture describes a confirmation flow that does not exist; security model is misrepresented. |
| Instruction | No allowlist/blacklist in prompt; no cwd/git/history context; thinking config hardcoded. |
| Session | Every request is single-turn; no conversation history in runner or TUI. |
| Runner | Duplicated event handling; inconsistent response assembly between stream and non-stream; exceptions flattened; no trace id or token logging. |
| TUI | Uses non-streaming path; no streaming UX. |
| Security | Auto-add to allowlist, no confirmation; only blacklist is a hard barrier. |
| Observability | No trace id, no token/cost visibility, no structured analytics. |
| Tools | Large flat set; instruction does not guide tool choice; get_user is heavy. |
| Testing | Runner and prompt not covered by integration or regression tests. |

---

## 4. Roadmap (What Would Need to Change)

This section is ordered by dependency and impact. It does not endorse a particular timeline; it states what must change for the system to match a stricter, more observable, and more maintainable design.

### 4.1 Correctness and Honesty

- **Fix documentation**: Rewrite the architecture and security sections so they describe the actual behavior (auto-add, no confirmation, blacklist-only hard block). Remove or correct any mention of `ToolContext.request_confirmation` and “confirmation flow.”
- **Document the real security model** in SECURITY.md or equivalent: what is enforced, where, and what the user is trusting (the model and the blacklist).

### 4.2 Instruction and Context

- **Inject allowlist and blacklist** into the system prompt (e.g. “Allowed: … Blocked: …”) so the model does not have to call tools to know the rules.
- **Inject minimal runtime context**: at least cwd and, if cheap, git branch. Optionally last N commands or a one-line “project hint.”
- **Expose thinking budget and include_thoughts** via config or env so users can tune cost and verbosity.

### 4.3 Session and Multi-Turn

- **Define a session abstraction**: one session per TUI instance (or per CLI “session” if ever supported). Persist or pass (role, content) for the last N turns.
- **Pass conversation history** into the runner so each request is multi-turn from the model’s perspective. This implies runner API changes and possibly ADK session usage changes.

### 4.4 Runner Quality

- **Single event-handling and response-assembly path**: one function that turns a stream of events into a response (and optional stream callbacks). Both `run_agent` and `run_agent_live` should use it.
- **Stable response contract**: document and test “final response string” and “ordered list of output parts” so both code paths and future clients rely on the same behavior.
- **Preserve exception types** or at least error codes (e.g. auth, rate limit, timeout) instead of wrapping everything in `RuntimeError`.
- **Add trace id** (and optionally request id) at entry and propagate to logs.

### 4.5 TUI and UX

- **Use the streaming path in the TUI**: call `run_agent_live` (or equivalent) and render tokens as they arrive so the user sees progress.
- **Improve error handling**: show a clear, actionable message and, where possible, distinguish network/auth errors from model errors.

### 4.6 Security (Optional but Recommended)

- **Configurable policy**: e.g. “require explicit user confirmation before adding a command to the allowlist” or “read-only mode (no execute_bash).” Implement only if the project commits to a stricter default or to giving users the choice.
- **High-risk patterns**: optional confirmation for commands matching a pattern (e.g. `rm -rf`, `dd`, `chmod 777`) even when on the allowlist.

### 4.7 Observability

- **Log token usage** when the provider or LiteLLM exposes it; optionally expose “session cost” or “today’s cost” in UI or CLI.
- **Structured tool-call logs** (e.g. JSON lines) so they can be queried or analyzed without scraping.

### 4.8 Testing

- **Runner integration tests**: run the full loop with a mocked model (fixed tool calls and text); assert response shape and that all part types are handled.
- **Instruction tests**: golden snippets or regression checks so that changes to `build_agent_instruction()` are visible and reviewable.

---

## 5. Conclusion

The current LLM integration works for single-turn, “one question, one answer” usage, but it is built on a number of questionable or undocumented choices: no real session, no context in the prompt, no streaming in the TUI, duplicated and inconsistent runner logic, and a security model that is both strict in code (blacklist) and permissive (auto-add to allowlist) and incorrectly described in the architecture doc. To “propel Flouri forward” in a way that is reliable, auditable, and cost-conscious, the priorities should be: **correct documentation**, **injected context and explicit allowlist/blacklist in the prompt**, **a single, well-tested runner path**, **streaming in the TUI**, and **session + history for multi-turn**. Without these, the system will remain fragile, hard to operate, and misleading to readers of the docs.
