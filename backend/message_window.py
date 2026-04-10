from langchain_core.messages import RemoveMessage
import tiktoken


_ENC = tiktoken.encoding_for_model("gpt-5")
ROUTING_MEMORY_TOKEN_BUDGET = 5000
ROUTING_MEMORY_DROP_FRACTION = 0.75


def _message_content_text(message) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    return str(content)


def approximate_message_tokens(message) -> int:
    return 3 + len(_ENC.encode(_message_content_text(message)))


def total_message_tokens(messages: list) -> int:
    return sum(approximate_message_tokens(message) for message in messages)


def build_fractional_prune_plan(
    messages: list,
    token_budget: int,
    drop_fraction: float = ROUTING_MEMORY_DROP_FRACTION,
) -> tuple[bool, list, list, list]:
    messages = messages or []
    if token_budget <= 0 or total_message_tokens(messages) <= token_budget:
        return (False, [], messages, [])

    drop_count = max(1, int(len(messages) * drop_fraction))
    retired = messages[:drop_count]
    kept = messages[drop_count:]
    removals = [RemoveMessage(id=message.id) for message in retired]
    return (True, retired, kept, removals)
