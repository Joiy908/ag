import asyncio
import unittest

from llama_index.core.llms import ChatMessage, MessageRole

from agent.my_llm import CozeLLM


class TestMyLLM(unittest.TestCase):
    """Test cases for the CozeLLM."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.llm = CozeLLM(user_id="test_user")

    def test_hello_message(self):
        """Test sending a simple 'hello' message to the LLM."""
        async def run_test():
            # Create a simple hello message
            messages = [
                ChatMessage(role=MessageRole.USER, content="hello")
            ]

            # Test the async streaming chat - await the generator first
            response_content = ""
            chat_gen = await self.llm.astream_chat(messages)
            async for response in chat_gen:
                if response.delta:
                    print(response.delta, end='', flush=True)
                    response_content += response.delta

            return response_content

        # Run the async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_test())
        finally:
            loop.close()

        # Verify we got some response
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)


if __name__ == '__main__':
    unittest.main()
