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


def append_with_fractional_prune(
    existing_messages: list,
    new_message,
    token_budget: int,
    drop_fraction: float = ROUTING_MEMORY_DROP_FRACTION,
):
    existing_messages = existing_messages or []
    candidate = [*existing_messages, new_message]
    if token_budget <= 0 or total_message_tokens(candidate) <= token_budget:
        return [new_message]

    drop_count = max(1, int(len(existing_messages) * drop_fraction))
    removals = [RemoveMessage(id=message.id) for message in existing_messages[:drop_count]]
    return [*removals, new_message]
