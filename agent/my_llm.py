from collections.abc import Sequence
from typing import Any

from cozepy import AsyncCoze
from llama_index.core.base.llms.types import (
    ChatMessage,
    ChatResponse,
    ChatResponseAsyncGen,
    CompletionResponse,
    MessageRole,
)
from llama_index.core.llms import (
    CompletionResponseGen,
    CustomLLM,
    LLMMetadata,
)
from llama_index.core.llms.callbacks import llm_chat_callback, llm_completion_callback

from agent import BOT_ID, acoze_client
from agent.coze_api import achat_stream


class CozeLLM(CustomLLM):
    # Define Pydantic fields
    acoze: AsyncCoze = acoze_client
    aconversation: Any = None
    bot_id: str = BOT_ID
    user_id: str = "default_user"

    def __init__(self, user_id: str = "default_user"):
        super().__init__()
        self.user_id = user_id

    @property
    def metadata(self) -> LLMMetadata:
        """Get LLM metadata."""
        return LLMMetadata(
            context_window=32000,
            num_output=16000,
            model_name='coze',
        )


    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        pass

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        # 在调试模式下打印彩色提示
        pass

    @llm_chat_callback()
    async def astream_chat(
        self,
        messages: Sequence[ChatMessage],
        **kwargs: Any,
    ) -> ChatResponseAsyncGen:
        # astream_complete + astream_chat
        async def gen() -> ChatResponseAsyncGen:
            assert self.messages_to_prompt is not None
            prompt = self.messages_to_prompt(messages)

            response = ""
            if not self.aconversation:
                self.aconversation = await self.acoze.conversations.create()
            async for c_type, delta in achat_stream(
                self.acoze, prompt, self.bot_id, self.user_id, self.aconversation.id
            ):
                if c_type == '0':
                    response += delta
                    yield ChatResponse(
                        message=ChatMessage(
                            role=MessageRole.ASSISTANT,
                            content=response,
                        ),
                        delta=delta,
                        raw=response,
                    )

        return gen()

