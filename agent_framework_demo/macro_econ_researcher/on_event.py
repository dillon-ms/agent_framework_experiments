from agent_framework import MagenticAgentDeltaEvent, MagenticAgentMessageEvent, MagenticCallbackEvent, MagenticFinalResultEvent, MagenticOrchestratorMessageEvent
from typing import Callable


async def get_magnetic_event_handler() -> Callable[[MagenticCallbackEvent], None]:
    """
    The `on_event` callback processes events emitted by the workflow.
    Events include: orchestrator messages, agent delta updates, agent messages, and final result events.
    """
    # State used by on_agent_stream callback

    last_stream_agent_id: str | None = None
    stream_line_open: bool = False
    def func(event: MagenticCallbackEvent) -> None:
        nonlocal last_stream_agent_id, stream_line_open
        if isinstance(event, MagenticOrchestratorMessageEvent):
            print(f"\n[ORCH:{event.kind}]\n\n{getattr(event.message, 'text', '')}\n{'-' * 26}")
        elif isinstance(event, MagenticAgentDeltaEvent):
            if last_stream_agent_id != event.agent_id or not stream_line_open:
                if stream_line_open:
                    print()
                print(f"\n[STREAM:{event.agent_id}]: ", end="", flush=True)
                last_stream_agent_id = event.agent_id
                stream_line_open = True
            print(event.text, end="", flush=True)
        elif isinstance(event, MagenticAgentMessageEvent):
            if stream_line_open:
                print(" (final)")
                stream_line_open = False
                print()
            msg = event.message
            if msg is not None:
                response_text = (msg.text or "").replace("\n", " ")
                print(f"\n[AGENT:{event.agent_id}] {msg.role.value}\n\n{response_text}\n{'-' * 26}")
        elif isinstance(event, MagenticFinalResultEvent):
            print("\n" + "=" * 50)
            print("FINAL RESULT:")
            print("=" * 50)
            if event.message is not None:
                print(event.message.text)
            print("=" * 50)
    return func