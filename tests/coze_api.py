import asyncio
import os
import unittest

from agent import BOT_ID, COZE_API_TOKEN, acoze_client
from agent.coze_api import achat_stream


class TestCozeAPI(unittest.TestCase):
    """Test cases for the coze_api module."""

    def setUp(self):
        self.acoze = acoze_client
        return super().setUp()

    def test_environment_variables(self):
        """Test that environment variables are loaded correctly."""
        # Note: These might be None in test environment, but should be defined
        self.assertIsNotNone(COZE_API_TOKEN or os.getenv("COZE_API_TOKEN"))
        self.assertIsNotNone(BOT_ID or os.getenv("BOT_ID"))

    def test_acoze_client_initialization(self):
        """Test that the Coze client can be properly initialized."""
        self.assertIsNotNone(self.acoze)
        # Check that it has the expected methods
        self.assertTrue(hasattr(self.acoze, 'chat'))
        self.assertTrue(hasattr(self.acoze.chat, 'stream'))

    def test_achat_stream_basic_flow(self):
        """Test the basic flow of achat_stream function."""
        async def run_test():
            results = []
            async for result in achat_stream(
                acoze=self.acoze,
                msg='hi, 1+1=?, only output the result number',
                bot_id=BOT_ID,
            ):
                results.append(result)
            return results

        # Run the async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(run_test())
        finally:
            loop.close()
        print(results)
        self.assertTrue('2' in results[0][1])

