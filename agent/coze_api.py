"""
Coze API streaming chat functionality.
"""
from cozepy import ChatEventType, Message


async def achat_stream(acoze, msg: str, bot_id: str, user_id: str = "default user", conversation_id: str | None = None):
    """
    Initiates chat. The response method is streaming.
    if there's not need to distinguish the context of the conversation(just a question and answer),
    skip the param of conversation_id
    Yields:
        tuple: A tuple containing the type of content and the content itself.
               The type can be (g,reasons), (0, texts), (d, end sign and token usage)
    """

    async for event in acoze.chat.stream(
        bot_id=bot_id,
        user_id=user_id,
        conversation_id=conversation_id,
        additional_messages=[Message.build_user_question_text(msg)],
    ):
        if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
            if event.message.reasoning_content:
                yield ('g', event.message.reasoning_content)
            else:
                yield ('0', event.message.content)
        elif event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
            yield ('d', f"token_usage: {event.chat.usage.token_count}")

