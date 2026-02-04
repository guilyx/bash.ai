"""Runner for executing agent interactions."""

import asyncio
import warnings

from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from ..agent import get_agent
from ..config import get_settings
from ..logging import initialize_session_log, log_conversation

# Suppress experimental warnings from Google ADK
warnings.filterwarnings("ignore", category=UserWarning, module="google.adk")


async def run_agent(
    prompt: str,
    allowed_commands: list[str] | None = None,
    blacklisted_commands: list[str] | None = None,
) -> str:
    """Run the agent with code execution capabilities.

    Args:
        prompt: The user's prompt
        allowed_commands: Optional list of allowed commands
        blacklisted_commands: Optional list of blacklisted commands

    Returns:
        The agent's response text
    """
    # Initialize session log if not already done
    initialize_session_log()

    # Log user message
    log_conversation("user", prompt)

    settings = get_settings()
    agent = get_agent(
        allowed_commands=allowed_commands,
        blacklisted_commands=blacklisted_commands,
    )

    # Create session
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=settings.app_name,
        user_id=settings.user_id,
        session_id=settings.session_id,
    )

    # Create runner
    runner = Runner(agent=agent, app_name=settings.app_name, session_service=session_service)

    # Create user content
    content = types.Content(role="user", parts=[types.Part(text=prompt)])

    final_response_text = ""
    output_parts = []

    try:
        async for event in runner.run_async(
            user_id=settings.user_id,
            session_id=settings.session_id,
            new_message=content,
        ):
            # Process ALL parts in the event to avoid warnings
            # Access content.parts directly to handle all part types
            if event.content and hasattr(event.content, "parts") and event.content.parts:
                for part in event.content.parts:
                    # Handle executable code
                    if hasattr(part, "executable_code") and part.executable_code:
                        # Code execution is happening - we'll wait for the result
                        pass
                    # Handle code execution results
                    elif hasattr(part, "code_execution_result") and part.code_execution_result:
                        result = part.code_execution_result
                        # Check outcome - handle both enum and string formats
                        outcome_value = result.outcome
                        if hasattr(outcome_value, "name"):
                            outcome_str = outcome_value.name
                        elif hasattr(outcome_value, "value"):
                            outcome_str = str(outcome_value.value)
                        else:
                            outcome_str = str(outcome_value)

                        if "OUTCOME_OK" in outcome_str.upper():
                            if result.output:
                                # Show execution output
                                output = result.output.strip()
                                if output:
                                    output_parts.append(output)
                        else:
                            # Show error output clearly
                            error_msg = result.output if result.output else "Execution failed"
                            output_parts.append(f"❌ Error: {error_msg}")
                    # Handle text parts (always process these)
                    elif hasattr(part, "text") and part.text:
                        text = part.text.strip()
                        if text:
                            output_parts.append(text)
                            # Also track for final response
                            if event.is_final_response():
                                final_response_text = text

    except Exception as e:
        raise RuntimeError(f"Error during agent run: {e}") from e

    # Combine all output parts
    if output_parts:
        # Remove duplicates while preserving order
        seen = set()
        unique_parts = []
        for part in output_parts:
            if part not in seen:
                seen.add(part)
                unique_parts.append(part)

        # If we have a final response that's not already in parts, add it
        if final_response_text and final_response_text not in seen:
            unique_parts.append(final_response_text)

        response = "\n\n".join(unique_parts)
    else:
        response = final_response_text if final_response_text else "No response generated."

    # Log agent response
    log_conversation("agent", response)

    return response


async def run_agent_live(
    prompt: str,
    allowed_commands: list[str] | None = None,
    blacklisted_commands: list[str] | None = None,
    stream_callback=None,
) -> str:
    """Run the agent with live streaming output.

    Args:
        prompt: The user's prompt
        allowed_commands: Optional list of allowed commands
        blacklisted_commands: Optional list of blacklisted commands
        stream_callback: Optional callback function(text) called for each text chunk

    Returns:
        The complete agent's response text
    """
    # Initialize session log if not already done
    initialize_session_log()

    # Log user message
    log_conversation("user", prompt)

    settings = get_settings()
    agent = get_agent(
        allowed_commands=allowed_commands,
        blacklisted_commands=blacklisted_commands,
    )

    # Create session
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=settings.app_name,
        user_id=settings.user_id,
        session_id=settings.session_id,
    )

    # Create runner
    runner = Runner(agent=agent, app_name=settings.app_name, session_service=session_service)

    # Create user content
    user_content = types.Content(role="user", parts=[types.Part(text=prompt)])

    # Append user event to session
    await session_service.append_event(session, Event(author="user", content=user_content))

    # Create live request queue
    live_request_queue = LiveRequestQueue()

    # Configure for TEXT streaming (not audio)
    run_config = RunConfig(response_modalities=["TEXT"])

    final_response_text = ""
    output_parts = []

    try:
        async for event in runner.run_live(
            user_id=settings.user_id,
            session_id=session.id,
            live_request_queue=live_request_queue,
            run_config=run_config,
        ):
            # Handle streaming text output - process ALL parts
            if event.content and hasattr(event.content, "parts") and event.content.parts:
                for part in event.content.parts:
                    # Handle text parts first (for streaming)
                    if hasattr(part, "text") and part.text:
                        text = part.text
                        final_response_text += text
                        # Call stream callback if provided
                        if stream_callback:
                            stream_callback(text)
                    # Handle executable code
                    elif hasattr(part, "executable_code") and part.executable_code:
                        # Code execution is happening - we'll wait for the result
                        pass
                    # Handle code execution results
                    elif hasattr(part, "code_execution_result") and part.code_execution_result:
                        result = part.code_execution_result
                        outcome_value = result.outcome
                        if hasattr(outcome_value, "name"):
                            outcome_str = outcome_value.name
                        elif hasattr(outcome_value, "value"):
                            outcome_str = str(outcome_value.value)
                        else:
                            outcome_str = str(outcome_value)

                        if "OUTCOME_OK" in outcome_str.upper():
                            if result.output:
                                output = result.output.strip()
                                if output:
                                    output_parts.append(output)
                                    if stream_callback:
                                        stream_callback(f"\n{output}\n")
                        else:
                            error_msg = result.output if result.output else "Execution failed"
                            error_text = f"❌ Error: {error_msg}"
                            output_parts.append(error_text)
                            if stream_callback:
                                stream_callback(f"\n{error_text}\n")

    except Exception as e:
        raise RuntimeError(f"Error during agent run: {e}") from e

    # Combine all output
    if output_parts:
        if final_response_text:
            output_parts.append(final_response_text)
        response = "\n\n".join(output_parts)
    else:
        response = final_response_text if final_response_text else "No response generated."

    # Log agent response
    log_conversation("agent", response)

    return response


def run_agent_sync(
    prompt: str,
    allowed_commands: list[str] | None = None,
    blacklisted_commands: list[str] | None = None,
) -> str:
    """Synchronous wrapper for run_agent.

    Args:
        prompt: The user's prompt
        allowed_commands: Optional list of allowed commands
        blacklisted_commands: Optional list of blacklisted commands

    Returns:
        The agent's response text
    """
    return asyncio.run(
        run_agent(
            prompt,
            allowed_commands=allowed_commands,
            blacklisted_commands=blacklisted_commands,
        )
    )


def run_agent_live_sync(
    prompt: str,
    allowed_commands: list[str] | None = None,
    blacklisted_commands: list[str] | None = None,
    stream_callback=None,
) -> str:
    """Synchronous wrapper for run_agent_live.

    Args:
        prompt: The user's prompt
        allowed_commands: Optional list of allowed commands
        blacklisted_commands: Optional list of blacklisted commands
        stream_callback: Optional callback function(text) called for each text chunk

    Returns:
        The complete agent's response text
    """
    return asyncio.run(
        run_agent_live(
            prompt,
            allowed_commands=allowed_commands,
            blacklisted_commands=blacklisted_commands,
            stream_callback=stream_callback,
        )
    )
