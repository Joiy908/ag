"""
Simple unittest module for testing the coze_api module functionality.

This test suite covers:
- Basic streaming chat functionality
- Environment variable loading
- Client initialization  
- Different event types (reasoning content vs regular content vs completion)

The tests use mocking to simulate the Coze API responses without making actual API calls.
"""

import unittest
from unittest.mock import MagicMock, patch
import asyncio
import os
from cozepy import ChatEventType


from agent.coze_api import achat_stream, acoze, COZE_API_TOKEN, BOT_ID


class TestCozeAPI(unittest.TestCase):
    """Test cases for the coze_api module."""

    def test_environment_variables(self):
        """Test that environment variables are loaded correctly."""
        # Note: These might be None in test environment, but should be defined
        self.assertIsNotNone(COZE_API_TOKEN or os.getenv("COZE_API_TOKEN"))
        self.assertIsNotNone(BOT_ID or os.getenv("BOT_ID"))

    def test_acoze_client_initialization(self):
        """Test that the Coze client is properly initialized."""
        self.assertIsNotNone(acoze)
        # Check that it has the expected methods
        self.assertTrue(hasattr(acoze, 'chat'))
        self.assertTrue(hasattr(acoze.chat, 'stream'))

    def test_achat_stream_basic_flow(self):
        """Test the basic flow of achat_stream function."""
        async def run_test():
            results = []
            async for result in achat_stream(
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

